def {{ field_getter_name }}(root, info):
    global variable_values

    if root is None:
        return None

    if info.return_type.is_type_of and not info.return_type.is_type_of(root, info):
        raise Exception(
            f'Expected value of type "{info.return_type}" but got: "{type(root)}".'
        )

    response = {}
    path = info.path
    {% for field_name, getter_name, resolver_name, info_name, field_def_name in sub_fields_info %}
    path.append('{{ field_name }}')
    child_info = {{ info_name }}
    field_ast = child_info.field_asts[0]
    field_def = {{ field_def_name }}

    arg_values = get_argument_values(
        field_def.args, field_ast.arguments, variable_values
    )

    update_resolve_info(child_info, root_value=root, context=info.context, variable_values=info.variable_values, path=path)
    resolved_child_value = {{ resolver_name }}(root, child_info, **arg_values)
    response['{{ field_name }}'] = {{ getter_name }}(resolved_child_value, child_info)
    path.pop()
    {% endfor %}
    return response
