import treelib
import json
from synctree.actions import define_action
import ast
import copy

class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


class Basebase:
    __slots__ = ['__branch__', '__subbranch__', '_node_identifier']

    def __init__(self, idnumber, **kwargs):
        self.idnumber = idnumber
        self._kwargs = kwargs
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.post_init()

    def post_init(self):
        """ override me as necessary """
        pass

    def _kvargs(self):
        try:
            return sorted({k:getattr(self, k) for k in dir(self) if not k.startswith('_')}.items(), key=lambda o: o[0])
        except TypeError:
            raise TypeError("No need to add property decorator to instance methods")

    @property
    def _to_json(self):
        """ 
        Returns a string
        """
        kwargs = copy.copy(self._kwargs)
        kwargs['idnumber'] = self.idnumber
        return json.dumps(kwargs, cls=SetEncoder)

    def __sub__(self, other):
        """
        Go through each variable/property that isn't a callable and check them out
        """

        # Limitation: We don't process (yet?) for exact equivalencies across both objects
        #             So you could have something defined as 'x' as a callable on this side
        #             but as a callable on other side, and you won't pick up any changes.
        if self._kvargs == other._kvargs:
            # This will be picked up in the key comparisons, so skip it
            return

        common = dict(idnumber=self.idnumber, obj=self, source=self, dest=other)

        attributes = [a for a in dir(self) if a == a.lstrip('_') and not callable(getattr(self, a))]
        for attribute in attributes:
            common.update(dict(attribute=attribute))
            try:
                this_attr = getattr(self, attribute)
            except AttributeError:
                yield define_action(method=f"err_no_attr:{self.__class__.__name__}.{attribute}", **common)
                continue
            try:
                that_attr = getattr(other, attribute)
            except AttributeError:
                yield define_action(method=f"err_no_attr:{other.__class__.__name__}.{attribute}", **common)
                continue

            if type(this_attr) != type(that_attr):
                yield define_action(method=f"err_integrity {type(this_attr)} != {type(that_attr)}", **common)
                continue

            if isinstance(this_attr, list):  # both are lists
                for to_add in set(this_attr) - set(that_attr):
                    yield define_action(value=to_add, method="add_{}_{}_to_{}".format(self.__subbranch__, attribute, other.__branch__), **common)
                for to_remove in set(that_attr) - set(this_attr):
                    yield define_action(value=to_remove, method="remove_{}_{}_from_{}".format(self.__subbranch__, attribute, other.__branch__), **common)

            elif isinstance(this_attr, set):  # both are sets
                for to_add in this_attr - that_attr:
                    yield define_action(value=to_add, method="add_{}_{}_to_{}".format(self.__subbranch__, attribute, other.__branch__), **common)
                for to_remove in that_attr - this_attr:
                    yield define_action(value=to_remove, method="remove_{}_{}_from_{}".format(self.__subbranch__, attribute, other.__branch__), **common)

            elif this_attr != that_attr:
                yield define_action(method="update_{}_{}".format(other.__subbranch__, attribute), value=this_attr, old_value=that_attr, **common)


    def __repr__(self):
        return f"<{self.__class__.__name__}({self.idnumber})>"


class Base(Basebase):
    """
    Prepares idnumber
    Reminder: All non-__ functions end up as properties
    """
    __slots__ = ['idnumber', '_kwargs']

    def __repr__(self):
        return "<{0.__class__.__name__}({0.idnumber})>".format(self)

    def __str__(self):
        return "<{0.idnumber} of {0.__subbranch__} in {0.__branch__}>".format(self)


