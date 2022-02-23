def {{ field_getter_name }}(root, info):
    child_info = {{ child_resolve_info_name }}
    update_resolve_info(child_info, root_value=root, context=info.context, variable_values=info.variable_values, path=info.path)
    result = {{ child_getter_name }}(root, child_info)

    if result is None:
        raise Exception(
            f"Cannot return null for non-nullable field {info.field_name}",
            info.path,
        )

    return result
