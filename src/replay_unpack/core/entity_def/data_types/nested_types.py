# coding=utf-8
"""
Dirty hack to simplify nested property and slices
Override list and dict types to store information about types
"""


class PyFixedDict(dict):
    """
    Emulate BigWorld type PyFixedDict
    """

    def __init__(self, attributes, *args, **kwargs):
        self._attributes = attributes
        super(PyFixedDict, self).__init__(*args, **kwargs)

    def get_field_name_for_index(self, index):
        return list(self._attributes.keys())[index]

    def get_field_type_for_index(self, index):
        return list(self._attributes.values())[index]


# TODO: hardcoded list len
class PyFixedList(list):
    """
    Emulate BigWorld type PyFixedList
    """

    def __init__(self, element_type, *args, **kwargs):
        super(PyFixedList, self).__init__(*args, **kwargs)
        if element_type is None:
            raise NotImplementedError("element_type must be not None")
        self._element_type = element_type

    def get_field_name_for_index(self, index):
        return index

    def get_element_type(self):
        return self._element_type
