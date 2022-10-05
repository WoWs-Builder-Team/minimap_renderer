# coding=utf-8


class PrettyPrintObjectMixin(object):
    def __repr__(self):
        if getattr(self, '__slots__', None):
            props = {k: getattr(self, k) for k in self.__slots__}
        else:
            props = self.__dict__
        return "<{}>: {}".format(self.__class__.__name__, props)
