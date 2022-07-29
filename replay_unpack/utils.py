def unpack_value(packed_value, value_min, value_max, bits):
    return packed_value / (2 ** bits - 1) * (abs(value_min) + abs(value_max)) - abs(value_min)


def unpack_values(packed_value, pack_pattern):
    values = []
    for i, pattern in enumerate(pack_pattern):
        min_value, max_value, bits = pattern
        value = packed_value & (2 ** bits - 1)

        values.append(unpack_value(value, min_value, max_value, bits))
        packed_value = packed_value >> bits
    try:
        assert packed_value == 0
    except AssertionError:
        pass
    return tuple(values)