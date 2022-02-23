from typing import Any, Optional

from .document import GraphQLCompiledDocument
from .compiler import CompilationContext
from graphql.language.parser import parse
from graphql import validate
from .type import CompileDocumentContext
from graphql.backend import GraphQLCoreBackend, GraphQLDocument

from .generate import generate_source


def build_compilation_context(
    schema,
    document_ast,
    root,
    operation_name,
    middleware,
) -> CompileDocumentContext:
    return CompilationContext(
        schema,
        document_ast,
        root,
        operation_name,
        middleware,
    )


class GraphQLFastBackend(object):
    def __init__(self, **options):
        super(GraphQLFastBackend, self).__init__(**options)

    def document_from_string(
        self,
        schema,
        query,
        root: Any = None,
        operation_name: Optional[str] = None,
        middleware: Optional[Any] = None,
        **options: Any,
    ) -> GraphQLDocument:
        document_ast = parse(query)
        validation_errors = validate(schema, document_ast)
        # TODO: Currently we don't support validation error handling
        if validation_errors:
            return GraphQLDocument(schema, query, document_ast, schema.execute)

        compilation_context = build_compilation_context(
            schema,
            document_ast,
            root,
            operation_name,
            middleware,
        )

        # TODO: We only support Query operations right now
        if compilation_context.operation.operation != "query":
            return GraphQLCoreBackend().document_from_string(schema, query)

        compile_document_context = generate_source(compilation_context)
        print("Schema generation successful")
        source = compile_document_context.code
        global_vars = compile_document_context.globals

        document = GraphQLCompiledDocument.from_code(
            schema, query, document_ast, source,
            global_vars,
        )
        return document
