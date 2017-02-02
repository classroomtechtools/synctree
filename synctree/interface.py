from abc import ABCMeta, abstractmethod
import inspect
import copy
import functools


class Interface(metaclass=ABCMeta):
    def __init__(self, idnumber, **kwargs):
        too_many = set(kwargs.keys()) - set(self._defaults.keys())
        if too_many != set():
            raise TypeError(f'On init, {self.__class__.__name__} passed unexpcted kwarg(s): {too_many}')
        self._kwargs = kwargs
        new_kwargs = copy.copy(self._defaults)
        new_kwargs.update(kwargs)
        self.idnumber = idnumber

        for key in new_kwargs:
            try:
                setattr(self, key, new_kwargs[key])
            except AttributeError:
                if key in self._defaults and not key in kwargs:
                    raise AttributeError(
                        f"Attr '{key}' in {self.__class__.__name__} has inconsistency in model and importer.\n"
                        "Model defined a default that is not present in kwargs passed to __init__"
                    )
                elif key in kwargs:
                    raise AttributeError(
                        f"Attr '{key}' in {self.__class__.__name__} has inconsistency in model and importer.\n" 
                        "Importer passed keyword on __init__ that has already defined by a property."
                    )
                else:
                    raise AttributeError(
                        f"Attr '{key}' in {self.__class__.__name__} has inconsistency in model and importer.\n"
                        "Root cause unknown"
                    ) 


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

