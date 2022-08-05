import pickle
import io
import builtins


safe_builtins = {
    "range",
    "complex",
    "set",
    "frozenset",
    "slice",
}


def unpack_value(packed_value, value_min, value_max, bits):
    return packed_value / (2**bits - 1) * (
        abs(value_min) + abs(value_max)
    ) - abs(value_min)


def unpack_values(packed_value, pack_pattern):
    values = []
    for i, pattern in enumerate(pack_pattern):
        min_value, max_value, bits = pattern
        value = packed_value & (2**bits - 1)

        values.append(unpack_value(value, min_value, max_value, bits))
        packed_value = packed_value >> bits
    try:
        assert packed_value == 0
    except AssertionError:
        pass
    return tuple(values)


def unpack_plane_id(packed_value: int) -> tuple:
    # avatar_id, index, purpose, departures
    bits = [32, 3, 3, 1]
    values = []
    for bit in bits:
        value = packed_value & (2**bit - 1)
        packed_value = packed_value >> bit
        values.append(value)
    return tuple(values)


class CamouflageInfo:
    def __init__(self, *args, **kwargs):
        pass


class PlayerMode:
    def __init__(self, *args, **kwargs):
        pass


class RestrictedUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        # Only allow safe classes from builtins.
        if module == "builtins" and name in safe_builtins:
            return getattr(builtins, name)
        elif module == "CamouflageInfo" and name == "CamouflageInfo":
            return CamouflageInfo
        elif module == "PlayerModeDef" and name == "PlayerMode":
            return PlayerMode
        # Forbid everything else.
        raise pickle.UnpicklingError(
            "global '%s.%s' is forbidden" % (module, name)
        )


def restricted_loads(data, **kwargs):
    """Helper function analogous to pickle.loads()."""
    return RestrictedUnpickler(io.BytesIO(data), **kwargs).load()
