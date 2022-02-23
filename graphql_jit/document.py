from typing import Any, Dict, Optional
from graphql.type.schema import GraphQLSchema
from graphql.backend import GraphQLDocument
import warnings


class GraphQLCompiledDocument(GraphQLDocument):
    @classmethod
    def from_code(
        cls,
        schema: GraphQLSchema,
        document_string: str,
        document_ast: Any,
        code: str,
        extra_global_vars: Optional[Dict[str, Any]] = None,
    ):
        """Creates a GraphQLQuery object from compiled code and the globals."""

        filename = "<document>"
        compiled_code = compile(code, filename, "exec")
        global_vars = {"__file__": compiled_code.co_filename}
        if extra_global_vars:
            global_vars.update(extra_global_vars)

        exec(compiled_code, global_vars)

        obj = object.__new__(cls)
        obj.schema = schema
        obj.code = code
        obj.execute_func = global_vars["execute"]
        obj.document_string = document_string
        obj.document_ast = document_ast
        return obj

    def execute(self, root=None, context=None, variables=None, *args, **kwargs):
        if root is None and "root_value" in kwargs:
            warnings.warn(
                "root_value has been deprecated. Please use root=... instead.",
                category=DeprecationWarning,
                stacklevel=2,
            )
            root = kwargs["root_value"]
        if context is None and "context_value" in kwargs:
            warnings.warn(
                "context_value has been deprecated. Please use context=... instead.",
                category=DeprecationWarning,
                stacklevel=2,
            )
            context = kwargs["context_value"]
        if variables is None and "variable_values" in kwargs:
            warnings.warn(
                "variable_values has been deprecated. Please use variables=... instead.",
                category=DeprecationWarning,
                stacklevel=2,
            )
            variables = kwargs["variable_values"]

        operation_name = kwargs.get("operation_name", None)
        return self.execute_func(
            root=root,
            context=context,
            variables=variables,
            operation_name=operation_name,
        )
