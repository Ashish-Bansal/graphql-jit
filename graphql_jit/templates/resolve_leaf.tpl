def {{ field_getter_name }}(result, info):
    if result is None:
        return None

    return_type = {{ object_type }}
    serialized_result = return_type.serialize(result)

    return serialized_result
