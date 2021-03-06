from .default_importer import DefaultImporter
import csv
import inspect
from contextlib import contextmanager
from collections import defaultdict

verbose = False


class CSVImporter(DefaultImporter):
    _settings = {
        'delimiter': ','
    }

    def init(self):
        delim = self.get_setting('delimiter') 
        if delim == '\\t':
            self.update_setting('delimiter', '\t')
        elif not delim:
            self.update_setting('delimiter', ',')

    def get_path(self):
        return self.get_setting('path')

    @contextmanager
    def reader(self):
        """
        Return the reader iterable object
        """
        resolved_path = self.get_path()

        fieldnames = self.get_setting('{}_columns'.format(self._subbranch.subbranchname), None)

        if not fieldnames:
            print(fieldnames)
            pass
            # Then it must be in the file itself, yes? TODO: Check for this, raise exception if not
            # It's doubtful that tools would export with the equivelent names that the syncing needs
            # so this probably needs a mapping feature
        else:
            fieldnames = fieldnames.split(' ')

        with open(resolved_path) as f:
            reader = csv.DictReader(f, 
                fieldnames=fieldnames,
                delimiter=self.get_setting('delimiter'))
            yield reader


class TranslatedCSVImporter:
    """
    Meta CSV importer used in situations where information for a particular branch
    is spread out over more than one file. 

    Usage:
    class MyStudentsImporter(TranslatedCSVImporter):
        translate = {'district': ['elementary', 'secondary']}
    """
    translate = {'': ['']}  # overrride
    klass = None
    csv_importers = defaultdict(list)

    def __init__(self, tree, branch, subbranch):
        """
        Mimick the DefaultImporter's __init__, passed onto TranslatedCSVImporter.__init__
        """
        self._tree = tree
        self._branch = branch
        for key, value in self.translate.items:
            inst = self.klass(tree, branch, subbranch)
            verbose and print("\tInside {} made instance of {} which has {}".format(self._branch.fullname, self.klass.__name__, inst._branch.fullname))

            # Verbose way of ensuring that value changes to the value at the time this is run
            # otherwise we would always return the same thing
            inst.file_hook = (lambda v: lambda p : p.replace(key, v))(value)
            # 

            self.csv_importers[self.__class__.__name__].append(inst)

    def reader(self):
        """
        Step through them all and call their reader method
        """
        verbose and print("Reading in with {} importers".format(len(self.csv_importers)))
        for csv_importer in self.csv_importers[self.__class__.__name__]:
            if inspect.isgeneratorfunction(csv_importer.reader):
                yield from csv_importer.reader()
            else:
                with csv_importer.reader() as reader:
                    yield from reader

