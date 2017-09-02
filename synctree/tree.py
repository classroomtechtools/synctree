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
                 jsonify_root_data=False,
                 raise_error_on_duplicates=True):
        """
        Makes a tree-like structure that mirrors, used to hold data used to send on operations
        to a synctree template
        """
        super().__init__()
        self.raise_error_on_duplicates = raise_error_on_duplicates
        self._relations = defaultdict(list)
        self.model_klass_list = model_klass_list or [[None] * len(subbranches)] * len(branches)
        self.importer_klass_list = importer_klass_list or [[None] * len(subbranches)] * len(branches)
        self._branch_class = branch_class if branch_class else Branch
        self._subbranches = subbranches  # store it away for when we need commands and the like

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
            for branch_index, branch in enumerate(self.branches):
                for subbranch_index, subbranch in enumerate(self.subbranches):
                    if len(self.importer_klass_list) == branch_index:
                        self.importer_klass_list.append([])
                    self.importer_klass_list[branch_index].append(importer_klass_list.format(branch=branch, branch_title=branch.title(), subbranch_title=subbranch.title()))

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
            # This feature is used in order to re-create for later
            rootdata = json.dumps(rootdata)

        # Make permanent root object, init clear-able branches and subbranches
        self.create_node(self.rootname, self.rootname, data=rootdata)
        self.init_branches_subbranches()
        #

    def init_branches_subbranches(self):

        for branch in self.branches:
            branch_obj = self._branch_class(self, branch, self._subbranches, self._importer_klasses[branch])   # use _subbranches, not self.subbranches
            self.create_node(
                branch, branch.lower(), parent=self.rootname, 
            )
            setattr(self, branch, branch_obj)
            for subbranch in self.subbranches:
                self.create_node(
                    subbranch, self.path_delim.join([branch, subbranch]), parent=branch.lower(),
                )

    def clear(self):
        """
        Remove branches, leaving root alone
        """
        for b in self.branches:
            branch = getattr(self, b)
            node_to_remove = f"{branch.branchname}"
            self.remove_subtree(node_to_remove)
        self.init_branches_subbranches()

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
        obj = klass(idnumber, **kwargs)

        # Augment the class name to hold branch and subbranch info
        obj.__branch__ = branch
        obj.__subbranch__ = subbranch

        key = self.keypath(*pth)
        parent =self.keypath(*pth[:-1])

        # Capture the error as appropriate
        try:
            result = self.create_node(idnumber, key, parent=parent, data=obj)
        except treelib.tree.DuplicatedNodeIdError:
            if self.raise_error_on_duplicates:
                raise  # TODO: use redefined exception
            else:
                return None
        # Augment this after creation so we can use it for tree operations
        # We have to get the result back
        obj._node_identifier = result.identifier
        
        return obj

    def store(self, path):
        with open(path, 'w') as _f:
            json.dump(json.loads(self.to_json()), _f, indent=4)

    def show(self, *args, **kwargs):
        if len(args) == 0:
            super().show(**kwargs)
        else:
            subbranch, idnumber, *_ = args
            kwargs['data_property'] = '_to_json'
            for branch in self.branches:
                print(f"{branch}/{subbranch}/{idnumber}:")
                path_to_node = f"{branch}{self.path_delim}{subbranch}{self.path_delim}{idnumber}"
                super().show(path_to_node, **kwargs)
                for subbranch_to in self._relations[subbranch]:
                    path_to_node = f"{branch}{self.path_delim}{subbranch_to}{self.path_delim}{idnumber}"
                    try:
                        super().show(path_to_node, **kwargs)
                    except treelib.tree.NodeIDAbsentError:
                        print(f"<no {subbranch_to}>")
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

    def register_relations(self, subbranches_from, subbranches_to):
        """
        Make it clear to the tree that idnumbers are shared between subbranches
        Useful for debugging
        """
        if not isinstance(subbranches_from, list):
            subbranches_from = [subbranches_from]
        if not isinstance(subbranches_to, list):
            subbranches_to = [subbranches_to]
        for subbranch_from in list(subbranches_from):
            for subbranch_to in list(subbranches_to):
                self._relations[subbranch_from].append(subbranch_to)


    def to_json(self, **kwargs):
        """
        Make the objects serializable
        """
        return json.dumps(self.to_dict(with_data=True, **kwargs), cls=JsonEncoder)

    def __repr__(self):
        """  """
        return f"SyncTree(branches={self.branches}, subbranches={self.subbranches})"

    def __call__(self, idnumber):
        """
        Output info and differences between objects
        """
        objs = []
        for branch in self.branches:
            br = getattr(self, branch)
            for obj in br(idnumber):
                objs.append( (br, obj) )

        getattr(self, self.branches[0]).is_source = True  # shortcut   

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
                source = sources.get(subbranch)
                if source is None:
                    continue
                for diff in source - obj:
                    if diff.old_value is not None:
                        output.append(f"{diff.method.upper()}: {diff.old_value} ==> {diff.value}")
                    else:
                        output.append(f"{diff.method.upper()}: ==> {diff.value} <==")
            if output:
                print('\n'.join(output))
            else:
                print("No Diffs")
        else:
            print("Cannot output difference since source is undetermined?")

    def __pos__(self):
        for branch in self.branches:
            +getattr(self, branch)

    def __str__(self):
        return "<{0.__class__.__name__}>".format(self)


