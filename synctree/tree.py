import treelib
from treelib import Tree
from synctree.base import Base
from synctree.branch import Branch
from synctree.subbranch import SubBranch
from synctree.utils import class_string_to_class

import json
from collections import defaultdict
from synctree.utils import initobj
import pickle


class JsonEncoder(json.JSONEncoder):
    def __init__(self, *args, **kwargs):
        self._current_subbranch = None
        super().__init__(*args, **kwargs)

    def default(self, obj):
        if isinstance(obj, Branch):
            return obj.to_json()
        elif isinstance(obj, SubBranch):
            return obj.to_json()
        elif isinstance(obj, Base):
            # All base objects become properties
            return obj._to_json
        return super().encode(self, obj)


class SyncTree(Tree):
    path_delim = '/'
    rootname = 'root'

    def __init__(self, 
                 branches, 
                 subbranches, 
                 model_klass_list: '( (classstr, classstr, ..), (classstr, classstr, ..) )' = None,
                 importer_klass_list: '( (classstr, classstr, ..), (classstr, classstr, ..) )' = None,
                 branch_class=None,
                 jsonify_root_data=True):
        """
        """
        super().__init__()
        self.model_klass_list = model_klass_list or [[None] * len(subbranches)] * len(branches)
        self.importer_klass_list = importer_klass_list or [[None] * len(subbranches)] * len(branches)
        self._branch_class = branch_class if branch_class else Branch

        # Prepare variables, remove any :off or like commands at this point
        self.branches = branches
        self.subbranches = [sb if not ':' in sb else sb.split(':')[0] for sb in subbranches]

        # If model or importer class is passed as a pattern string, coerce it into a list of a list
        if isinstance(self.model_klass_list, str):
            self.model_klass_list = []
            for i, branch in enumerate(self.branches):
                for j, subbranch in enumerate(self.subbranches):
                    if len(self.model_klass_list) == i:
                        self.model_klass_list.append([])
                    self.model_klass_list[i].append(model_klass_list.format(branch=branch, branch_title=branch.title(), subbranch_title=subbranch.title()))

        if isinstance(self.importer_klass_list, str):
            self.importer_klass_list = []
            for i, branch in enumerate(self.branches):
                for j, subbranch in enumerate(self.subbranches):
                    if len(self.importer_klass_list) == i:
                        self.importer_klass_list.append([])
                    self.importer_klass_list[i].append(importer_klass_list.format(branch=branch, branch_title=branch.title(), subbranch_title=subbranch.title()))

        # Prepare self._model_klasses
        if sum(map(len, self.model_klass_list)) != len(self.branches) * len(self.subbranches):
            raise ValueError("Must be equal")
        if sum(map(len, self.model_klass_list)) != sum(map(len, self.importer_klass_list)):
            raise ValueError("Still not equal")

        self._model_klasses = defaultdict(lambda : defaultdict(list))
        self._importer_klasses = defaultdict(lambda : defaultdict(list))

        # Convert prepared into actual classes through importation process
        for i1, klasses in enumerate(self.model_klass_list):
            b = branches[i1]  # branch
            for i2, _ in enumerate(klasses):
                sb = self.subbranches[i2]
                klass_str = self.model_klass_list[i1][i2]
                self._model_klasses[b][sb] = class_string_to_class(klass_str)
                klass_str = self.importer_klass_list[i1][i2]
                self._importer_klasses[b][sb] = class_string_to_class(klass_str)

        rootdata = dict(
            branches = self.branches,
            subbranches = self.subbranches,
            model_klass_list = self.model_klass_list,
            importer_klass_list = self.importer_klass_list,
        )

        if jsonify_root_data:
            rootdata = json.dumps(rootdata)

        self.create_node(self.rootname, self.rootname, data=rootdata)
        for branch in self.branches:
            i = branches.index(branch)
            branch_obj = self._branch_class(self, branch, subbranches, self._importer_klasses[branch])   # use subbranches, not self.subbranches
            self.create_node(
                branch, branch.lower(), parent=self.rootname, 
            )
            setattr(self, branch, branch_obj)
            for subbranch in self.subbranches:
                self.create_node(
                    subbranch, self.path_delim.join([branch, subbranch]), parent=branch.lower(),
                )

    def keypath(self, *pth):
        """
        Converts raw information into the path
        """
        return self.path_delim.join( pth )

    def new(self, *pth: ['branch', 'subranch', 'idnumber'], **kwargs):
        """ 
        Create a new object 
        """
        branch, subbranch, idnumber = pth

        klass = self._model_klasses[branch][subbranch] or initobj(branch, subbranch, **kwargs)
        try:
            obj = klass(idnumber, **kwargs)
        except TypeError:
            raise TypeError('Expecting {0._properties} but got {1}'.format(klass, kwargs))

        # Augment the class name to hold branch and subbranch info
        obj.__branch__ = branch
        obj.__subbranch__ = subbranch

        key = self.keypath(*pth)
        parent =self.keypath(*pth[:-1])

        # Augment this after creation so we can use it for tree operations
        # We have to get the result back
        result = self.create_node(idnumber, key, parent=parent, data=obj)
        obj._node_identifier = result.identifier
        #

    def store(self, path):
        with open(path, 'w') as _f:
            json.dump(json.loads(self.to_json()), _f, indent=4)

    @classmethod
    def from_file(cls, path):
        """
        Reads in file (created by self.store or other)
        And adds
        """
        
        # Read in rootdata info, and create instance based on that
        with open(path, 'r') as _f:
            j = json.load(_f)

        rootdata_string = j[cls.rootname]['data']
        rootdata = json.loads(rootdata_string)

        # initiate with same values provided to them
        t = SyncTree(rootdata['branches'], rootdata['subbranches'],
            model_klass_list=rootdata['model_klass_list'],
            importer_klass_list=rootdata['importer_klass_list']
        )

        with open(path, 'r') as _f:
            j = json.load(_f)

        root = j[cls.rootname]
        for branch_list in root['children']:
            for branch in branch_list.keys():
                for subbranch_list in branch_list[branch].get('children', []):
                    for subbranch in subbranch_list.keys():
                        for item in subbranch_list[subbranch].get('children', []):
                            for idnumber in item.keys():
                                data = item[idnumber]['data']
                                kwargs = json.loads(data)
                                t.new(branch, subbranch, idnumber, **kwargs)
        return t

    def to_json(self, **kwargs):
        """
        Make the objects serializable
        """
        return json.dumps(self.to_dict(with_data=True, **kwargs), cls=JsonEncoder)

    def clear(self):
        """
        Remove items in all subbranches of branches
        Does not change the branches/subbranches
        """
        self.remove_subtree('root')

        # for b in self.branches:
        #     branch = getattr(self, b)
        #     for s in branch.subbranches:
        #         subbranch = getattr(branch, s)
        #         for item in subbranch.get_objects():
        #             self.remove_node(item._node_identifier)

    def __call__(self, idnumber):
        """
        Output info and differences between objects
        """
        objs = []
        for branch in self.branches:
            br = getattr(self, branch)
            for obj in br(idnumber):
                objs.append( (br, obj) )

        sources = {}
        for br, obj in objs:
            if br.is_source:
                subbranch = obj.__subbranch__
                sources[subbranch] = obj

        if sources:
            output = []
            for br, obj in objs:
                if br.is_source:
                    continue
                subbranch = obj.__subbranch__
                source = sources[subbranch]
                for diff in source - obj:
                    output.append(str(diff))
            if output:
                print('\n'.join(output))
            else:
                print("No Diffs")
        else:
            print("No source?")

    def __pos__(self):
        for branch in self.branches:
            +getattr(self, branch)

    def __str__(self):
        return "<{0.__class__.__name__}>".format(self)


