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

def test_basic():
    branches = ['csv', 'db']
    #subbranches = ['students', 'staff', 'enrollments']
    subbranches = {
        'students': ['name', 'grade'],
        'staff': ['name', 'passport_id'],
        'course': ['name'],
        'enrollments': ['user_idnumber', 'course']
    }

    s = SyncTree(branches, subbranches)

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



if __name__ == "__main__":

    test_init(inspect=True)