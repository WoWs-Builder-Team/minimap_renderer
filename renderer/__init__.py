import importlib


def get_renderer(version: str):
    """
    Gets the renderer for the corresponding game version.
    :param version: Game version.
    :return: A Renderer class.
    """
    return getattr(importlib.import_module(f".{version}", package="renderer.versions"), "Renderer")
