import pytest

from synctree.tree import SyncTree
from synctree.base import Base
from synctree.branch import Branch
from synctree.importers.default_importer import DefaultImporter
from synctree.interface import property_interface
student_properties = 'lastfirst last first'
import json

# Classes we need
class Student(Base):
    """
    Stuff common to both sides
    """
    def name(self):
        return self.first + ' ' + self.last

class Enrollment(Base):
    pass

@property_interface(student_properties, lastfirst="")
class AStudent(Student):

    def last(self):
        return self.lastfirst.split(',')[0].strip()

    def first(self):
        return self.lastfirst.split(',')[1].strip()

@property_interface(student_properties, first="", last="")
class MStudent(Student):
    """
    """
    def lastfirst(self):
        return self.last + ', ' + self.first

@property_interface('courses', courses=[])
class AEnrollment(Enrollment):
    pass

@property_interface('courses', courses=[])
class MEnrollment(Enrollment):
    pass

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

def test_init(inspect=False):

    branches = ['autosend', 'moodle']
    subbranches = ['students', 'staff', 'enrollments']

    s = SyncTree(
        branches,
        subbranches,
        ( (AStudent, None, AEnrollment), (MStudent, None, MEnrollment) ),
        ( (None, None, None), (None, None, None) ),
        jsonify_root_data = False  # turn off
    )

    new_enrollment = '9B'
    s.new('autosend', 'enrollments', '99999', courses=['9A', new_enrollment])
    s.new('moodle', 'enrollments', '99999', courses=['9A'])
    result = list(s.moodle - s.autosend)
    # Add and an update?
    assert len(result) == 1
    assert result[0].value == new_enrollment
    s.clear()
    # Branches/subbranches should survive a clear
    assert s.branches == branches
    assert s.subbranches == subbranches

    old_enrollment = '9C'
    s.new('autosend', 'enrollments', '99999', courses=['9A'])
    s.new('moodle', 'enrollments', '99999', courses=['9A', old_enrollment])
    result = list(s.moodle - s.autosend)

    assert len(result) == 1
    assert result[0].value == old_enrollment

    t = SyncTree(
        branches,
        subbranches,
        ( (AStudent, None, AEnrollment), (MStudent, None, MEnrollment) ),
        ( (AStudentImp, None, AEnrollmentImp), (MStudentImp, None, MEnrollmentImp) ),
        jsonify_root_data = False  # turn off
    )
    +t
    # Test that the opposite side has parameters and same values from original side
    assert t.moodle.students.get('99999').lastfirst == 'Shmoe, Joe'
    assert t.autosend.students.get('99999').first == 'Joe'
    assert t.autosend.students.get('99999').last == 'Shmoe'

    assert t.autosend.enrollments.get('99999').courses == ['9A', '9B']  # test the list adding feature
    assert t.autosend.enrollments.get('11111').courses == {'10A', '10B'}  # test the set adding feature

def test_templates():

    from synctree.templates import DefaultTemplate
    from synctree.hijacker import coerce_returns_to_list
    from synctree.utils import extend_template_exceptions
    from synctree.actions import define_action

    from synctree.results import \
        successful_result, \
        unsuccessful_result, \
        dropped_action

    import gns

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
        _reporter_class = MyReporter
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
            undeclared_variable # raises runtime error, should be eaten up

    template = NewTemplate()

    # Test that new decorator has been put into place
    assert template.test_this_one.__name__ == "test_this_one"
    assert isinstance(template.test_this_one, coerce_returns_to_list)
    assert template.test_this_one() == [1]
    assert template.not_this_one() == 1

    # Test we get expected results

    action = define_action(method='success')
    with pytest.raises(ExceptionSuccess):
        template(action)

    action = define_action(method='fail')
    with pytest.raises(ExceptionFail):
        template(action)

    action = define_action(method='raises_exception')
    with pytest.raises(ExceptionException): 
        template(action)


if __name__ == "__main__":

    test_templates()