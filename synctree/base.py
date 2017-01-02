import treelib
import json
from synctree.utils import return_action

class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)

class Base:
    """
    Prepares idnumber
    Reminder: All non-__ functions end up as properties
    """

    def __init__(self, expected_kwargs, defaults, idnumber, **kwargs):
        if set(kwargs.keys()) - set(expected_kwargs) != set():
            raise TypeError("unexpected kwargs passed:")
        self.idnumber = idnumber
        self._kwargs = kwargs
        for key in kwargs:
            setattr(self, key, kwargs[key])

    def __repr__(self):
        return "<{0.__class__.__name__}({0.idnumber})>".format(self)

    def __str__(self):
        return "<{0.idnumber} of {0.__subbranch__} in {0.__branch__}>".format(self)

    def _kvargs(self):
        try:
            return sorted({k:getattr(self, k) for k in dir(self) if not k.startswith('_')}.items(), key=lambda o: o[0])
        except TypeError:
            raise TypeError("No need to add property decorator to instance methods")

    def _to_json(self):
        """ 
        Returns a string
        """
        return json.dumps(self._kwargs, cls=SetEncoder)

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

        common = dict(idnumber=self.idnumber, source=self, dest=other)

        attributes = [a for a in dir(self) if a == a.lstrip('_') and not callable(getattr(self, a))]
        for attribute in attributes:
            common.update(dict(attribute=attribute))
            try:
                this_attr = getattr(self, attribute)
            except AttributeError:
                yield return_action(message="err_no_attr:{}".format(attribute), **common)
                continue
            try:
                that_attr = getattr(other, attribute)
            except AttributeError:
                yield return_action(message="err_no_attr:{}".format(attribute), **common)
                continue

            if type(this_attr) != type(that_attr):
                yield return_action(message="err_integrity", **common)
                continue

            if isinstance(this_attr, list):  # both are lists
                for to_add in set(this_attr) - set(that_attr):
                    yield return_action(value=to_add, message="add_{}_{}_to_{}".format(self.__subbranch__, attribute, other.__branch__), **common)
                for to_remove in set(that_attr) - set(this_attr):
                    yield return_action(value=to_remove, message="remove_{}_{}_from_{}".format(self.__subbranch__, attribute, other.__branch__), **common)

            elif isinstance(this_attr, set):  # both are sets
                for to_add in this_attr - that_attr:
                    yield return_action(value=to_add, message="add_{}_{}_to_{}".format(self.__subbranch__, attribute, other.__branch__), **common)
                for to_remove in that_attr - this_attr:
                    yield return_action(value=to_remove, message="remove_{}_{}_from_{}".format(self.__subbranch__, attribute, other.__branch__), **common)

            elif this_attr != that_attr:
                yield return_action(message="update_{}_{}".format(other.__subbranch__, attribute), value=this_attr, old_value=that_attr, **common)

