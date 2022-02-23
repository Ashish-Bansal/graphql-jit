def {{ field_getter_name }}(list_of_items, info):
    if list_of_items is None:
        return None

    if not isinstance(list_of_items, Iterable):
        raise Exception(
            f"User Error: expected iterable, but found : {type(list_of_items)} {info.path}"
        )

    result = []

    path = info.path
    for index, item in enumerate(list_of_items):
        path.append(index)
        child_info = {{ child_resolve_info_name }}
        update_resolve_info(child_info, root_value=item, context=info.context, variable_values=info.variable_values, path=path)
        result.append({{ field_getter_name }}_item(item, child_info))
        path.pop()
    return result
