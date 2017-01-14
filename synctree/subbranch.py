from collections import defaultdict
import inspect
from treelib.tree import DuplicatedNodeIdError as Duplicated
from synctree.importers.default_importer import DefaultImporter

class SubBranch:
    def __init__(self, branch, subbranchname, importer):
        self.branch = branch
        self.subbranchname = subbranchname
        self.parent_keypath = self.branch.tree.keypath(self.branch.branchname, self.subbranchname)
        self._importer_klass = importer

    @property
    def path_delim(self):
        return self.branch.tree.path_delim

    @property
    def idnumbers(self):
        return {
            key.split(self.path_delim)[-1] \
                for key in self.branch.tree._nodes \
                    if not key.endswith(self.subbranchname) and key.startswith(self.parent_keypath + self.path_delim)
            }

    @property
    def subtree(self):
        """
        Returns the subtree, which has to be dynamically derived each time
        otherwise will end up with missing elements
        """
        return self.branch.tree.subtree(self.parent_keypath)

    def get(self, idnumber, node_key=None):
        """
        @returns None if does not exist
        """
        node_key = self.branch.tree.keypath(self.branch.branchname, self.subbranchname, idnumber)
        try:
            # Don't use subtree here
            return self.branch.tree.get_node(node_key).data
        except AttributeError:
            return None

    def get_objects(self):
        _nodes = self.branch.tree._nodes
        for node in [_nodes[key] for key in _nodes.keys() if key.startswith(self.parent_keypath + '/')]:
            if node.data is not None:
                yield node.data
        # for node in self.subtree.leaves():
        #     if node.data is not None:  # if data is None, then it is probably a subbranch item itself
        #         yield node.data

    def make(self, idnumber, **kwargs):
        """
        Makes the object, returns it
        If it is a duplicate, contacts the importer on what to do with it
        """
        try:
            return self.branch.tree.new(self.branch.branchname, self.subbranchname, idnumber, **kwargs)
        except Duplicated:
            return self.importer.resolve_duplicate(self.get(idnumber), **kwargs)

    @property
    def importer(self):
        """ Returns the importer, or DefaultImporter is not available """
        if not hasattr(self, '_importer'):
            params = [self.branch.tree, self.branch, self]
            if self._importer_klass is None:
                self._importer = DefaultImporter(*params)
            else:
                self._importer = self._importer_klass(*params)
        return self._importer

    def process_kwargs(self, **kwargs_in):
        """
        Responsible for handling the kwargs args
        Manages _temp in cases with lists
        """
        kwargs = self.importer.kwargs_preprocessor(kwargs_in)
        if kwargs is None:
            return
        has_list_value = len([1 for k in kwargs.keys() if isinstance(kwargs[k], (list, set))]) > 0
        if not 'idnumber' in kwargs:
            idnumber = str(self._index)
            self._index += 1
        else:
            idnumber = kwargs['idnumber']
            del kwargs['idnumber']
        if has_list_value:
            self._temp[idnumber].append(kwargs)
        else:
            obj = self.make(idnumber, **kwargs)

    def __pos__(self):          # +
        self._temp = defaultdict(list)
        self._index = 0

        if inspect.isgeneratorfunction(self.importer.reader):
            # We are using a generator
            for kwargs_in in self.importer.reader():
                self.process_kwargs(**kwargs_in)
        else:
            # We have a context manager
            with self.importer.reader() as reader:
                for kwargs_in in reader:
                    self.process_kwargs(**kwargs_in)

        if len(self._temp.keys()) > 0:
            for idnumber in self._temp.keys():
                prepared = {}
                kwargs_list = self._temp[idnumber]
                for item in kwargs_list:
                    for list_key in [k for k in item.keys() if isinstance(item[k], list)]:
                        if list_key not in prepared:
                            prepared[list_key] = []
                        prepared[list_key].extend(item[list_key])
                        del item[list_key]
                    for set_key in [k for k in item.keys() if isinstance(item[k], set)]:
                        if set_key not in prepared:
                            prepared[set_key] = set()
                        prepared[set_key].update(item[set_key])
                        del item[set_key]

                    # Add the additional ones, too
                    prepared.update(item)

                    self.make(idnumber, **prepared)

        if hasattr(self.importer, 'on_import_complete'):
            self.importer.on_import_complete()

    def __sub__(self, other):   # -
        """
        idnumbers not found in other
        """
        yield from self.idnumbers - other.idnumbers

    def __and__(self, other):   # &
        """
        Common idnumbers
        """
        yield from self.idnumbers & other.idnumbers

    def __repr__(self):
        return "{0.__class__.__name__}({0.branch}, {0.subbranchname})".format(self)

class SubBranchOff(SubBranch):
    """
    A particular subbranch that does not take part in the differences mechnaism, and excludes it from sync commands
    by overriding the operators that yield values 
    """

    def __sub__(self, other):   # -
        """
        idnumbers not found in other
        """
        yield from []

    def __and__(self, other):   # &
        """
        Common idnumbers
        """
        yield from []
