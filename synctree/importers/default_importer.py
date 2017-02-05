"""
An abstract importer, can be used as is, but does nothing
"""


class DefaultImporter:
    _settings = None

    def __init__(self, tree, branch, subbranch):
        self._tree = tree
        self._branch = branch
        self._subbranch = subbranch
        self.init()

    def kwargs_preprocessor(self, kwargs_in):
        """
        Chance for the importer to augment or adjust kwargs as they come in
        Returning None instructs the wheel to skip
        By default, just return the original
        """
        return kwargs_in

    def get_setting(self, key, default=None):
        return self._settings.get(key, default)

    def update_setting(self, key, value):
        self._settings[key] = value

    def init(self):
        """
        Inspect settings variables if needed
        """
        pass

    def reader(self):
        """
        Can be generator, if not generator, then assumed to be contextmanager
        Must be underscore, because generators are not callables, and we use underscores to skip them
        """
        yield from []

    def resolve_duplicate(self, original_obj, **kwargs):
        """
        Called by the importer
        """
        pass

