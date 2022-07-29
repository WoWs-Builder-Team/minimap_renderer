#!/usr/bin/python
# coding=utf-8
__author__ = "Aleksandr Shyshatsky"

import importlib
import os

from replay_unpack.core.entity_def.definitions import Definitions

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def get_definitions(version):
    return Definitions(os.path.join(BASE_DIR, 'versions', version.replace('.', '_')))


def get_controller(version):
    """
    Get real controller class by game version.
    """
    try:
        module = importlib.import_module('.versions.%s' % version, package=__package__)
    except ModuleNotFoundError:
        raise RuntimeError("version %s is not supported currently" % version)

    try:
        conrtoller = module.BattleController()
    except AttributeError:
        raise AssertionError("battle controller for version %s "
                             "should contain BattleController class" % version)
    return conrtoller
