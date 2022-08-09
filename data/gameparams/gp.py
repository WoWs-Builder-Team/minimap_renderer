import json
import pickle
import struct
import zlib
import os
import io


class RenameUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        renamed_module = module
        if module == "GameParams":
            renamed_module = "data.gameparams.GameParams"

        return super(RenameUnpickler, self).find_class(renamed_module, name)


def get_data(gp_type: str):
    with open(
        os.path.join(os.getcwd(), "resources", "GameParams.data"), "rb"
    ) as f:
        gp_data: bytes = f.read()
        gp_data: bytes = struct.pack("B" * len(gp_data), *gp_data[::-1])
        gp_data: bytes = zlib.decompress(gp_data)
        gp_data_dict: dict = RenameUnpickler(
            io.BytesIO(gp_data), encoding="latin1"
        ).load()
    return filter(
        lambda g: g.typeinfo.type == gp_type, gp_data_dict[0].values()
    )
