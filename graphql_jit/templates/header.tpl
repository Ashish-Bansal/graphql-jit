from graphql.execution.values import get_variable_values
from graphql import GraphQLObjectType
from graphql.execution.values import get_argument_values
from graphql.execution.base import ResolveInfo
from collections.abc import Iterable
from graphql.execution import ExecutionResult

def update_resolve_info(info, root_value=None, context=None, variable_values=None, path=None):
    if root_value:
        info.root_value = root_value

    if context:
        info.context = context

    if path:
        info.path = path

    if variable_values:
        info.variable_values = variable_values
