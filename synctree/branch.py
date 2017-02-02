from synctree.subbranch import SubBranch, SubBranchOff, SubBranchNarrow
from synctree.actions import define_action

from synctree import Wheel
from functools import partial

import ast
import weakref

class NoImporter:
    pass


class Branch:
    _subbranch_class = SubBranch

    def __init__(self, tree, branchname: None, subbranches: None, importers=None):
        self.is_source = False
        self.tree = weakref.proxy(tree)
        self.branchname = branchname or ''
        subbranches = subbranches or []
        self.subbranches = [sb if ':' not in sb else sb.split(':')[0] for sb in subbranches]
        self.importers = importers or {sb: None for sb in subbranches}
        for subbranch in subbranches:
            if ":" in subbranch:
                subbranch, command = subbranch.split(':')
                if command.lower() == 'off':
                    subbranch_class = SubBranchOff
                elif command:
                    command_dict = eval(command)
                    to_narrow = command_dict[self.branchname]
                    subbranch_class = SubBranchNarrow(to_narrow)
            else:
                subbranch_class = self._subbranch_class
            setattr(self, subbranch, subbranch_class(self, subbranch, self.importers[subbranch]))
        self.parent_keypath = self.tree.keypath(self.branchname)

    @property
    def subtree(self):
        if not hasattr(self, '_subtree'):
            self._subtree = self.tree.subtree(self.parent_keypath)
        return self._subtree

    @property
    def idnumbers(self):
        return {n.tag for n in self.subtree.all_nodes() if n.tag not in [*self.subbranches, self.branchname]}

    def get_from_subbranches(self, idnumber, subbranches: ['second_branch', 'first_branch']):
        """
        Find an object in any of the passed subbranches
        """
        for subbranchname in subbranches:
            subbranch = getattr(self, subbranchname)
            r = subbranch.get(idnumber)
            if r:
                return r
        return None

    def __call__(self, idnumber):
        """
        Output info and differences between objects
        """
        contains_key = self.tree.keypath('', idnumber)
        ret = []
        output_strs = []
        for node_key in self.tree._nodes.keys():
            node = self.tree.get_node(node_key)
            if node.data and node_key.startswith(self.branchname):
                output_strs.append(str(node.data))
                ret.append(node.data)
        if output_strs:
            print(self.branchname.upper())
            print('\n'.join(output_strs))
            print('-----')
        return ret

    def __sub__(self, other):
        """
        Generator that returns action items that instructs the mechnism how to proceed to align the data
        Goes through each subbranch and does set comparisons to determine items that:
        1) Exist on the leftside only (and are thus "new")
        2) Exist on the rightside only (and are thus "old")
        3) Exist in both, but have different values for different items (and thus need to be modified)
        """
        if self.subbranches != other.subbranches:
            raise TypeError("Subbranches cannot be compared with unlike subbranches")

        for subbranch in self.subbranches:
            leftsubbranch = getattr(self, subbranch)
            rightsubbranch = getattr(other, subbranch)

            for idnumber in leftsubbranch - rightsubbranch:
                # items only appearing in left
                l = leftsubbranch.get(idnumber)
                yield define_action(idnumber=idnumber, value=l, obj=l, source=l, dest=None, method='new_{}'.format(subbranch))

            for idnumber in rightsubbranch - leftsubbranch:
                # items only appearing in right
                r = rightsubbranch.get(idnumber)
                yield define_action(idnumber=idnumber, value=r, obj=r, source=None, dest=r, method='old_{}'.format(subbranch))

            for idnumber in leftsubbranch & rightsubbranch:
                # common items
                lobj = leftsubbranch.get(idnumber)
                robj = rightsubbranch.get(idnumber)
                yield from lobj - robj

    def __pos__(self):
        for subbranch in self.subbranches:
            +getattr(self, subbranch)

    def wheel(self, other):
        yield from self - other

    def __gt__(self, other):
        """
        Returns a generator that implements the __or__ (bitwise or) or pipe
        """
        call_generator = partial(self.wheel, other)
        return Wheel(call_generator)

    def __repr__(self):
        return "{0.__class__.__name__}({0.tree}, {0.branchname}, {0.subbranches})".format(self)

class MoodleBranch:
    pass
