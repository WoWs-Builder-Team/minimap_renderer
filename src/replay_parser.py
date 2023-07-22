# coding=utf-8
from typing import BinaryIO
import logging
import os
import json
import struct
import zlib

from replay_unpack.clients import wot, wows
from replay_unpack.replay_reader import (
    ReplayReader,
    ReplayInfo,
    REPLAY_SIGNATURE,
)


class DefaultEncoder(json.JSONEncoder):
    def default(self, o):
        try:
            return o.__dict__
        except AttributeError:
            return str(o)


class CustomReader(ReplayReader):
    # noinspection PyMissingConstructor
    def __init__(self, fp: BinaryIO, dump_binary=False):
        self._dump_binary_data = dump_binary
        self._fp = fp
        self._type = "wowsreplay"

    def get_replay_data(self) -> ReplayInfo:
        """
        Get open info about replay
        (stored as Json at the beginning of file)
        and closed one
        (after decrypt & decompress);
        :rtype: tuple[dict, str]
        """
        if self._fp.read(4) != REPLAY_SIGNATURE:
            raise ValueError(
                "File %s is not a valid replay" % self._replay_path
            )

        blocks_count = struct.unpack("i", self._fp.read(4))[0]

        block_size = struct.unpack("i", self._fp.read(4))[0]
        engine_data = json.loads(self._fp.read(block_size))

        extra_data = []
        for i in range(blocks_count - 1):
            block_size = struct.unpack("i", self._fp.read(4))[0]
            _ = self._fp.read(block_size)

            # data = json.loads(self._fp.read(block_size))
            # extra_data.append(data)

        # noinspection PyUnresolvedReferences
        decrypted_data = zlib.decompress(
            self._ReplayReader__decrypt_data(self._fp.read())
        )

        if self._dump_binary_data:
            self._save_decrypted_data(decrypted_data)

        return ReplayInfo(
            game="wows",
            engine_data=engine_data,
            extra_data=extra_data,
            decrypted_data=decrypted_data,
        )


class ReplayParser(object):
    BASE_PATH = os.path.dirname(__file__)

    def __init__(
        self,
        fp: BinaryIO,
        strict: bool = False,
        raw_data_output=None,
        logging_level: int = logging.ERROR,
    ):
        self._fp = fp
        self._is_strict_mode = strict
        self._reader = CustomReader(fp)
        self._raw_data_output = raw_data_output
        logging.basicConfig(level=logging_level)
        root = logging.getLogger()
        root.setLevel(logging.ERROR)

    def get_info(self):
        replay = self._reader.get_replay_data()

        error = None
        try:
            hidden_data = self._get_hidden_data(replay)
        except Exception as e:
            if isinstance(e, RuntimeError):
                error = str(e)
            logging.exception(e)
            hidden_data = None

            # raise error in strict mode
            if self._is_strict_mode:
                raise

        return dict(
            open=replay.engine_data,
            extra_data=replay.extra_data,
            hidden=hidden_data,
            error=error,
        )

    def _get_hidden_data(self, replay: ReplayInfo):
        if replay.game == "wot":
            # 'World of Tanks v.1.8.0.2 #252'
            version = ".".join(
                replay.engine_data.get("clientVersionFromXml")
                .replace("World of Tanks v.", "")
                .replace(" ", ".")
                .replace("#", "")
                .split(".")[:3]
            )
            player = wot.ReplayPlayer(version)
        elif replay.game == "wows":
            player = wows.ReplayPlayer(
                replay.engine_data.get("clientVersionFromXml")
                .replace(" ", "")
                .split(",")
            )
        else:
            raise NotImplementedError

        if self._raw_data_output:
            with open(self._raw_data_output, "wb") as fp:
                fp.write(replay.decrypted_data)

        player.play(replay.decrypted_data, self._is_strict_mode)
        return player.get_info()


def main(replay, strict_mode, raw_data_output):
    logging.basicConfig(level=getattr(logging, namespace.log_level))

    with open(replay, "rb") as fp:
        replay_info = ReplayParser(
            fp, strict=strict_mode, raw_data_output=raw_data_output
        ).get_info()

    import pickle

    with open("data.dat", "wb") as f:
        pickle.dump(replay_info["hidden"]["replay_data"], f)
    # print(json.dumps(replay_info, indent=1, cls=DefaultEncoder))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--replay", type=str, required=True)
    parser.add_argument(
        "--log_level",
        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
        required=False,
        default="ERROR",
    )
    parser.add_argument("--strict_mode", action="store_true", required=False)
    parser.add_argument(
        "--raw_data_output",
        help="File where raw replay content (decoded and decompressed) will be written",
        required=False,
        default=None,
    )

    namespace = parser.parse_args()
    main(namespace.replay, namespace.strict_mode, namespace.raw_data_output)
