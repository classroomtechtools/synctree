from abc import ABCMeta, abstractmethod
import inspect
import copy
import functools

class Interface(metaclass=ABCMeta):
    def __init__(self, idnumber, **kwargs):
        too_many = set(kwargs.keys()) - set(self._defaults.keys())
        if too_many != set():
            raise TypeError('On init, {} passed unexpcted kwarg(s): {}'.format(self.__class__.__name__, ",".join(list(too_many))))
        self._kwargs = kwargs
        new_kwargs = copy.copy(self._defaults)
        new_kwargs.update(kwargs)
        self.idnumber = idnumber
        for key in new_kwargs:
            try:
                setattr(self, key, new_kwargs[key])
            except AttributeError:
                raise AttributeError("Cannot set {} attr ".format(key))

class property_interface(object):
    """
    Class decorator
    """

    def __init__(self, properties, **defaults):
        """
        If there are decorator arguments, the function
        to be decorated is not passed to the constructor!
        """
        self.properties = [p for p in properties.split(' ') if p]
        self.remaining_props = set(self.properties) - set(defaults.keys())
        self.defaults = defaults

    def __call__(self, klass):
        """
        If there are decorator arguments, __call__() is only called
        once, as part of the decoration process! You can only give
        it a single argument, which is the function object.
        """
        attrs = {prop: property(abstractmethod(lambda : None)) for prop in self.remaining_props}
        attrs.update({prop: property(function) for prop, function in inspect.getmembers(klass) if not prop.startswith('__')})
        t = type(klass.__name__, (Interface, klass), attrs)

        # These are used in Interface.__init__ above
        t._properties = self.properties
        t._defaults = self.defaults
        return t

