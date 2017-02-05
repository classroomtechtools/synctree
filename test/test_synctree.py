import pytest

from synctree.tree import SyncTree
from synctree.base import Base
from synctree.branch import Branch
from synctree.importers.default_importer import DefaultImporter
student_properties = ['lastfirst', 'last', 'first']
import json


class Student(Base):
    """
    Stuff common to both sides
    """
    __slots__ = student_properties

    @property
    def name(self):
        return self.first + ' ' + self.last


class Enrollment(Base):
    __slots__ = ['courses']


class AStudent(Student):
    __slots__ = []

    @property
    def last(self):
        return self.lastfirst.split(',')[0].strip()

    @property
    def first(self):
        return self.lastfirst.split(',')[1].strip()


class MStudent(Student):
    """
    """
    __slots__ = []

    @property
    def lastfirst(self):
        return self.last + ', ' + self.first


class AEnrollment(Enrollment):
    __slots__ = []


class MEnrollment(Enrollment):
    __slots__ = []


class AStudentImp(DefaultImporter):
    def reader(self):
        yield dict(idnumber='99999', lastfirst="Shmoe, Joe")
        yield dict(idnumber='11111', lastfirst="Student, New")


class MStudentImp(DefaultImporter):
    def reader(self):
        yield dict(idnumber='99999', first="Joe", last="Shmoe")
        yield dict(idnumber='zzzzz', first="Withdrawn", last="Student")


class AEnrollmentImp(DefaultImporter):
    def reader(self):
        yield dict(idnumber='99999', courses=['9A'])
        yield dict(idnumber='99999', courses=['9B'])
        yield dict(idnumber='11111', courses=set(['10A']))
        yield dict(idnumber='11111', courses=set(['10B']))


class MEnrollmentImp(DefaultImporter):
    def reader(self):
        yield dict(idnumber='99999', courses=['9A'])


def test_wrappedinit():
    from synctree.base import initobj
    kwargs = dict(hi='hi')
    tupfactory = initobj('autosend', 'students', **kwargs)
    tup = tupfactory('9999', **kwargs)
    assert tup.idnumber == '9999'
    assert tup.hi == 'hi'


def test_barebones():
    """ Test various init routines """
    branches = ['autosend', 'moodle']
    subbranches = ['students', 'staff', 'enrollments']

    tree = SyncTree(branches, subbranches)

    tree.new('autosend', 'enrollments', '99999', courses=['9A', '10B'])


def test_init(inspect=False):

    branches = ['autosend', 'moodle']
    subbranches = ['students', 'staff', 'enrollments']

    tree = SyncTree(
        branches,
        subbranches,
        ((AStudent, None, AEnrollment), (MStudent, None, MEnrollment)),
        ((None, None, None), (None, None, None)),
        jsonify_root_data=False  # turn off
    )

    new_enrollment = '9B'
    tree.new('autosend', 'enrollments', '99999', courses=['9A', new_enrollment])
    tree.new('moodle', 'enrollments', '99999', courses=['9A'])
    result = list(tree.moodle - tree.autosend)
    # Add and an update?
    assert len(result) == 1
    assert result[0].value == new_enrollment
    tree.clear()
    # Branches/subbranches should survive a clear
    assert tree.branches == branches
    assert tree.subbranches == subbranches

    old_enrollment = '9C'
    tree.new('autosend', 'enrollments', '99999', courses=['9A'])
    tree.new('moodle', 'enrollments', '99999', courses=['9A', old_enrollment])
    result = list(tree.moodle - tree.autosend)

    assert len(result) == 1
    assert result[0].value == old_enrollment

    tree = SyncTree(
        branches,
        subbranches,
        ((AStudent, None, AEnrollment), (MStudent, None, MEnrollment)),
        ((AStudentImp, None, AEnrollmentImp), (MStudentImp, None, MEnrollmentImp)),
        jsonify_root_data=False  # turn off
    )

    +tree
    # Test that the opposite side has parameters and same values from original side
    assert tree.moodle.students.get('99999').lastfirst == 'Shmoe, Joe'
    assert tree.autosend.students.get('99999').first == 'Joe'
    assert tree.autosend.students.get('99999').last == 'Shmoe'

    assert tree.autosend.enrollments.get('99999').courses == ['9A', '9B']  # test the list adding feature
    assert tree.autosend.enrollments.get('11111').courses == {'10A', '10B'}  # test the set adding feature


def test_narrowing():
    """
    Adding a feature which will only return a certain idnumber
    """
    b1, b2, sb1, sb2 = ('branch1', 'branch2', 'subbranch1:dict(branch1=["000"],branch2=["000"])', 'subbranch2')
    brnchs = [b1, b2]
    sbbrnchs = [sb1, sb2]

    tree = SyncTree(
        brnchs,
        sbbrnchs,
    )
    tree.new(b1, sb1.split(':')[0], '000', change='this')
    tree.new(b2, sb1.split(':')[0], '000', change='that')
    tree.new(b1, sb1.split(':')[0], '001', change='nothing')
    tree.new(b2, sb1.split(':')[0], '001', change='nothing')

    tree.new(b1, sb2, '999', change='this')
    tree.new(b2, sb2, '999', change='that')
    tree.new(b1, sb2, '888', change='nothing')
    tree.new(b2, sb2, '888', change='nothing')

    subbranch = getattr(getattr(tree, b1), sb2)
    assert len(subbranch.idnumbers) == 2  # nothing tunrned off

    subbranch = getattr(getattr(tree, b1), sb1.split(':')[0])
    assert len(subbranch.idnumbers) == 1  # not 2
    assert subbranch.get('001') != None  # still has it though
    assert len(list(subbranch)) == 2  # not 1, because iterating still has them

    branch1 = getattr(tree, b1)
    branch2 = getattr(tree, b2)

    list(branch1 - branch2)

    # Test iteration on subbranches
    assert len(list(tree.branch1.subbranch1)) == 2

def test_templates():

    from synctree.templates import DefaultTemplate, LoggerReporter
    from synctree.hijacker import coerce_returns_to_list
    from synctree.utils import extend_template_exceptions
    from synctree.actions import define_action

    from synctree.results import \
        successful_result, \
        unsuccessful_result, \
        dropped_action


    class ExceptionException(Exception): pass
    class ExceptionSuccess(Exception): pass
    class ExceptionFail(Exception): pass
    class ExceptionNotImplemented(Exception): pass

    class MyReporter:

        def exception(self, action, result):
            raise ExceptionException("exception_method")

        def success(self, action, result):
            raise ExceptionSuccess("success_method")

        def fail(self, action, result):
            raise ExceptionFail("fail_method")

        def not_implemented(self, action, result):
            """
            Override if this
            """
            raise ExceptionNotImplemented("not_implemented")

    class NewTemplate(DefaultTemplate):
        _reporter = MyReporter
        _exceptions = extend_template_exceptions('not_this_one result')

        def test_this_one(self):
            return 1  # not a list

        def not_this_one(self):
            return 1  # not a list

        def success(self, action):
            return successful_result(method=action.method, info="called")

        def fail(self, action):
            return unsuccessful_result(method=action.method, info="called")

        def dropped(self, action):
            return dropped_action(method=action.method, info='none')

        def raises_exception(self):
            undeclared_variable  # raises runtime error, should be eaten up

    template = NewTemplate()

    # Test that new decorator has been put into place
    assert template.test_this_one.__name__ == "test_this_one"
    assert isinstance(template.test_this_one, coerce_returns_to_list)
    assert template.test_this_one() == [1]
    assert template.not_this_one() == 1

    # Test the reporter, which for us will just raise exceptions
    action = define_action(method='success')
    with pytest.raises(ExceptionSuccess):
        template(action)

    action = define_action(method='fail')
    with pytest.raises(ExceptionFail):
        template(action)

    action = define_action(method='raises_exception')
    with pytest.raises(ExceptionException):
        template(action)

    from synctree.templates import LoggerTemplate
    from collections import defaultdict


    class MyBuiltReporter(LoggerReporter):

        def success(self, action, result):
            self._log[action.source.__subbranch__][action.idnumber].append(result)


    class MyLoggerTemplate(LoggerTemplate):
        _reporter = MyBuiltReporter
        _test_this_string = 'test_this_string'

        def update_subbranch1_change(self, action):
            return successful_result(method=self._test_this_string)


    class MyTree(SyncTree):
        pass


    b1, b2, sb1, sb2 = ('branch1', 'branch2', 'subbranch1', 'subbranch2')
    brnchs = [b1, b2]
    sbbrnchs = [sb1, sb2]
    tree = SyncTree(brnchs, sbbrnchs)
    tree.new(b1, sb1, '000', change='this')
    tree.new(b2, sb1, '000', change='that')

    results = list(getattr(tree, b1) > getattr(tree, b2))
    assert len(results) == 1
    # results[0].method = 
    template = MyLoggerTemplate()
    (getattr(tree, b1) > getattr(tree, b2)) | template

    assert template.reporter._log[sb1]['000'][0].method == template._test_this_string

    # test to ensure we save the log as we go
    template = MyLoggerTemplate()
    assert template.reporter._log[sb1]['000'][0].method == template._test_this_string


if __name__ == "__main__":

    test_templates()