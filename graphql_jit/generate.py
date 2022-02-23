from typing import List, Optional, Tuple, Union
from graphql.error.base import GraphQLError
from graphql.execution.base import ResolveInfo

from graphql.language.ast import Field
from .compiler import CompilationContext
from graphql.execution.executor import get_operation_root_type
from graphql.execution.utils import (
    get_field_def,
    default_resolve_fn,
    get_field_entry_key,
)
from graphql.type.definition import (
    GraphQLEnumType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
)
import functools


from .type import CompileDocumentContext
from .utils import render_template


def serialise_path(path: List[str], prefix: Optional[str] = None) -> str:
    path = [prefix] + path if prefix else path
    return "_".join(path)


def get_resolver_name_for_path(path: List[str]) -> str:
    return serialise_path(path, prefix="resolve")


def get_getter_name_for_path(path: List[str]) -> str:
    return serialise_path(path, prefix="get")


def get_resolve_info_name_for_path(path: List[str]) -> str:
    return serialise_path(path, prefix="resolve_info")

def get_field_def_name_for_path(path: List[str]) -> str:
    return serialise_path(path, prefix="get_field_defs")


def merge_compile_document_context_pair(
    child: CompileDocumentContext,
    parent: CompileDocumentContext,
) -> CompileDocumentContext:
    parent_code = parent.code
    child_code = child.code

    parent_globals = parent.globals
    child_globals = child.globals

    parent_globals.update(child_globals)
    code = child_code + "\n\n" + parent_code
    return CompileDocumentContext(
        code=code,
        globals=parent_globals,
    )


def merge_compile_document_contexts(
    contexts: List[CompileDocumentContext],
) -> CompileDocumentContext:
    return functools.reduce(
        lambda a, b: merge_compile_document_context_pair(a, b),
        contexts,
    )


def generate_based_on_type(
    compilation_context: CompilationContext,
    object_type: GraphQLObjectType,
    field_ast: List[Field],
    path: List[Union[int, str]],
) -> CompileDocumentContext:
    if isinstance(object_type, GraphQLNonNull):
        return generate_non_null_selection(
            compilation_context,
            object_type,
            field_ast,
            path,
        )

    if isinstance(object_type, GraphQLObjectType):
        return generate_object_selection(
            compilation_context,
            object_type,
            field_ast,
            path,
        )

    if isinstance(object_type, GraphQLList):
        return generate_list_selection(
            compilation_context,
            object_type,
            field_ast,
            path,
        )

    if isinstance(object_type, (GraphQLScalarType, GraphQLEnumType)):
        return generate_leaf_selection(
            compilation_context,
            object_type,
            field_ast,
            path,
        )

    return CompileDocumentContext(code="", globals={})


def generate_non_null_selection(
    compilation_context: CompilationContext,
    object_type: GraphQLObjectType,
    field_ast: List[Field],
    path: List[Union[int, str]],
) -> CompileDocumentContext:
    item_type = object_type.of_type
    field_name = f"{field_ast.name.value}-item"
    child_resolve_info = ResolveInfo(
        field_name,
        field_ast,
        item_type,
        object_type,
        schema=compilation_context.schema,
        operation=compilation_context.operation,
        fragments=compilation_context.fragments,
        # Only available at runtime.
        root_value=None,
        variable_values=None,
        context=None,
        path=None,
    )

    new_path = path + ["non_null"]
    child_getter_name = get_getter_name_for_path(new_path)
    child_resolve_info_name = get_resolve_info_name_for_path(new_path)

    getter_name = get_getter_name_for_path(path)
    code = render_template(
        "resolve_non_null.tpl",
        field_getter_name=getter_name,
        child_resolve_info_name=child_resolve_info_name,
        child_getter_name=child_getter_name,
    )

    child_compile_document_context = generate_based_on_type(
        compilation_context, item_type, field_ast, new_path
    )
    return merge_compile_document_contexts(
        [
            child_compile_document_context,
            CompileDocumentContext(code=code, globals={child_resolve_info_name: child_resolve_info}),
        ]
    )


def generate_leaf_selection(
    compilation_context: CompilationContext,
    object_type: GraphQLObjectType,
    field_ast: List[Field],
    path: List[Union[int, str]],
) -> CompileDocumentContext:
    getter_name = get_getter_name_for_path(path)

    object_type_name = serialise_path(path + [object_type.name])
    code = render_template(
        "resolve_leaf.tpl", field_getter_name=getter_name, object_type=object_type_name
    )
    return CompileDocumentContext(code=code, globals={object_type_name: object_type})


def generate_list_selection(
    compilation_context: CompilationContext,
    object_type: GraphQLObjectType,
    field_ast: List[Field],
    path: List[Union[int, str]],
) -> CompileDocumentContext:
    item_type = object_type.of_type
    field_name = f"{field_ast.name.value}-item"
    child_resolve_info = ResolveInfo(
        field_name,
        field_ast,
        item_type,
        object_type,
        schema=compilation_context.schema,
        operation=compilation_context.operation,
        fragments=compilation_context.fragments,
        # Only available at runtime.
        root_value=None,
        variable_values=None,
        context=None,
        path=None,
    )

    new_path = path + ["item"]
    child_resolve_info_name = get_resolve_info_name_for_path(new_path)
    getter_name = get_getter_name_for_path(path)

    code = render_template(
        "resolve_list.tpl",
        field_getter_name=getter_name,
        child_resolve_info_name=child_resolve_info_name,
    )

    child_compile_document_context = generate_based_on_type(
        compilation_context, item_type, field_ast, new_path
    )
    return merge_compile_document_contexts(
        [
            child_compile_document_context,
            CompileDocumentContext(code=code, globals={child_resolve_info_name: child_resolve_info}),
        ]
    )


def generate_object_selection(
    compilation_context: CompilationContext,
    object_type: GraphQLObjectType,
    field_ast: Field,
    path: List[Union[int, str]],
) -> CompileDocumentContext:
    globals_dict = {}
    child_compile_document_contexts = []

    sub_fields_info: List[Tuple[str, str, str, str, str]] = []

    subfield_asts = compilation_context.get_sub_fields(object_type, field_ast)
    for subfield_ast in subfield_asts:
        field_name = subfield_ast.name.value

        field_def = get_field_def(compilation_context.schema, object_type, field_name)
        if not field_def:
            raise Exception("Unable to find definition for field", field_name)

        child_object_type = field_def.type
        resolve_fn = field_def.resolver or default_resolve_fn
        resolve_fn_with_middleware = compilation_context.get_field_resolver(resolve_fn)
        new_path = list(path) + [field_name]
        getter_name = get_getter_name_for_path(new_path)
        resolver_name = get_resolver_name_for_path(new_path)
        resolve_info_name = get_resolve_info_name_for_path(new_path)
        field_def_name = get_field_def_name_for_path(new_path)
        response_name = get_field_entry_key(subfield_ast)
        sub_fields_info.append(
            (response_name, getter_name, resolver_name, resolve_info_name, field_def_name)
        )

        resolve_info = ResolveInfo(
            field_name,
            [subfield_ast],
            child_object_type,
            object_type,
            schema=compilation_context.schema,
            operation=compilation_context.operation,
            fragments=compilation_context.fragments,
            # Only available at runtime.
            root_value=None,
            variable_values=None,
            context=None,
            path=None,
        )
        globals_dict[resolver_name] = resolve_fn_with_middleware
        globals_dict[field_def_name] = field_def
        globals_dict[resolve_info_name] = resolve_info

        child_compile_document_context = generate_based_on_type(
            compilation_context, child_object_type, subfield_ast, new_path
        )
        child_compile_document_contexts.append(child_compile_document_context)

    field_getter_name = get_getter_name_for_path(path)
    driver_code = render_template(
        "resolve_object.tpl",
        field_getter_name=field_getter_name,
        sub_fields_info=sub_fields_info,
    )

    parent_context = CompileDocumentContext(code=driver_code, globals=globals_dict)
    contexts = child_compile_document_contexts + [parent_context]
    return merge_compile_document_contexts(contexts)


def generate_source(
    compilation_context: CompilationContext,
) -> CompileDocumentContext:
    schema = compilation_context.schema
    operation = compilation_context.operation
    operation_type = get_operation_root_type(schema, operation)
    path = ["root"]
    operation_context = generate_based_on_type(
        compilation_context, operation_type, operation, path
    )

    field_getter_name = get_getter_name_for_path(path)
    header_code = render_template("header.tpl", field_getter_name=field_getter_name)
    driver_code = render_template("query.tpl", field_getter_name=field_getter_name)
    return merge_compile_document_contexts(
        [
            CompileDocumentContext(code=header_code, globals={}),
            operation_context,
            CompileDocumentContext(
                code=driver_code, globals={"schema": schema, "operation": operation}
            ),
        ]
    )
