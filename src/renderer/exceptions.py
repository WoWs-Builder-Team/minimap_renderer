class MapLoadError(Exception):
    """Raised when there's an error at loading the map file(s).

    Args:
        Exception (_type_): _description_
    """
    pass


class MapManifestLoadError(Exception):
    """Raised when there's an error at parsing the manifest file.

    Args:
        Exception (_type_): _description_
    """
    pass
