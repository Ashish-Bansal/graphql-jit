from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from graphql.error.base import GraphQLError
from graphql.execution.utils import collect_fields
from graphql.language import ast
from graphql.language.ast import Document
from graphql.pyutils.default_ordered_dict import DefaultOrderedDict
from graphql.type.definition import GraphQLField, GraphQLObjectType
from graphql.type.introspection import Field
from graphql.type.schema import GraphQLSchema
import itertools


class CompilationContext(object):
    """Data that must be available at all points during query compilation."""

    def __init__(
        self,
        schema: GraphQLSchema,
        document_ast: Document,
        root_value: Any,
        operation_name: Optional[str],
        middleware: Optional[Any],
    ) -> None:
        operation = None
        fragments = {}

        for definition in document_ast.definitions:
            if isinstance(definition, ast.OperationDefinition):
                if not operation_name and operation:
                    raise GraphQLError(
                        "Must provide operation name if query contains multiple operations."
                    )

                if (
                    not operation_name
                    or definition.name
                    and definition.name.value == operation_name
                ):
                    operation = definition
            elif isinstance(definition, ast.FragmentDefinition):
                fragments[definition.name.value] = definition
            else:
                raise GraphQLError(
                    u"GraphQL cannot execute a request containing a {}.".format(
                        definition.__class__.__name__
                    ),
                    definition,
                )

        if not operation:
            if operation_name:
                raise GraphQLError(
                    u'Unknown operation named "{}".'.format(operation_name)
                )

            else:
                raise GraphQLError("Must provide an operation.")

        self.schema = schema
        self.fragments = fragments
        self.document_ast = document_ast
        self.root_value = root_value
        self.operation = operation
        self.argument_values_cache: Dict[
            Tuple[GraphQLField, Field], Dict[str, Any]
        ] = {}
        self.middleware = middleware
        self._subfields_cache: Dict[
            Tuple[GraphQLObjectType, Tuple[Field, ...]], DefaultOrderedDict
        ] = {}

    def get_field_resolver(self, field_resolver: Callable) -> Callable:
        if not self.middleware:
            return field_resolver
        return self.middleware.get_field_resolver(field_resolver)

    def get_sub_fields(
        self, parent_type: GraphQLObjectType, parent_field_ast: Field
    ) -> List[Field]:
        k = parent_type, parent_field_ast
        if k not in self._subfields_cache:
            subfield_asts = DefaultOrderedDict(list)
            visited_fragment_names: Set[str] = set()
            selection_set = parent_field_ast.selection_set
            if selection_set:
                subfield_asts = collect_fields(
                    self,
                    parent_type,
                    selection_set,
                    subfield_asts,
                    visited_fragment_names,
                )
            subfield_asts_list = itertools.chain.from_iterable(subfield_asts.values())
            self._subfields_cache[k] = subfield_asts_list
        return self._subfields_cache[k]
