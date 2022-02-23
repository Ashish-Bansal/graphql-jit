variable_values = {}

def execute(root=None, context=None, variables=None, operation_name=None):
    global schema
    global operation
    global variable_values

    variable_values = variables or {}

    root = root or {}
    info = ResolveInfo(
        field_name="root",
        field_asts=[],
        return_type=GraphQLObjectType("root", {}),
        parent_type=GraphQLObjectType("query", {}),
        schema=schema,
        fragments={},
        root_value=root,
        operation=operation,
        variable_values=variable_values,
        context=context,
        path=["root"],
    )
    result = {{ field_getter_name }}(root, info)
    return ExecutionResult(data=result, errors=None)
