
# synctree
Framework for re-modeling information from a source into a new format.

### QUICKSTART

The framework is initialized with the creation of a tree structure, which has `branches` and `subbranches`. The idea is that the branches represent data points, such as sources or destinations, and the subbranches represent the kinds of objects that are to be synced (in the model).


```python
from synctree import SyncTree
synctree = SyncTree(
    ['source', 'destination'], 
    ['students', 'staff', 'classes', 'enrollments'],
    raise_error_on_duplicates=False
)

synctree.show()
```

    root
    ├── destination
    │   ├── classes
    │   ├── enrollments
    │   ├── staff
    │   └── students
    └── source
        ├── classes
        ├── enrollments
        ├── staff
        └── students
    


Notice that the tree is mirrored: Both branches have the same number of subbranches. Leaves of each subbranch, which can be manually creaeted with `SyncTree.new` represent objects in a model:


```python
synctree.new('source', 'students', '111', name="NoName", grade=7)
synctree.new('destination', 'students', '111', name="NoName", grade=6)
```

This creates an object in the tree in both the source and the destination. This emulates a situation where a student has gone from grade 6 into grade 7, but the destination (a database, whatever) has not been updated with this information yet. The package does have a means to read in information from CSVs, databases, but for the sake of explanation these manual calls give us the gist.


```python
synctree.show()
```

    root
    ├── destination
    │   ├── classes
    │   ├── enrollments
    │   ├── staff
    │   └── students
    │       └── 111
    └── source
        ├── classes
        ├── enrollments
        ├── staff
        └── students
            └── 111
    


We can also use ```SyncTree.show``` to inspect the actual objects created:


```python
synctree.show('students', '111')
```

    source/students/111:
    {"name": "NoName", "grade": 7, "idnumber": "111"}
    
    destination/students/111:
    {"name": "NoName", "grade": 6, "idnumber": "111"}
    


Synctree knows how to discover the differences in attributes (in our case, the change in grade), and reports it:


```python
from pprint import pprint
# operator overload means "find the difference"
action_objects = list(synctree.source - synctree.destination)

for item in action_objects:
    # action objects are namedtuples, so convert for readability
    pprint(dict(item._asdict()))
```

    {'attribute': 'grade',
     'dest': <DestinationStudents(111)>,
     'idnumber': '111',
     'method': 'update_students_grade',
     'obj': <SourceStudents(111)>,
     'old_value': 6,
     'source': <SourceStudents(111)>,
     'value': 7}


Notice that Synctree has identified the values that have changed, and created a string "update_students_grade" which we can use to operate upon. Let's make a class with a method that corresponds to that string:


```python
from synctree.templates import DefaultTemplate
class Template(DefaultTemplate):
    def update_students_grade(self, action):
        print("Update!")
```

By creating a class with the method ```Template.update_students_grade```, we can use a simple dispatcher to flow our control that way.


```python
template = Template()
for action_item in synctree.source - synctree.destination:
        method = getattr(template, action_item.method)
        method(action_item)
```

    Update!


We can automate this by refining our template's method to return a ```Template.successful_result```, which gives us the ability to use more operator overloads to handle the dispatch for us:


```python
from synctree.templates import DefaultTemplate
from synctree.results import successful_result

class Template(DefaultTemplate):
    def update_students_grade(self, action):
        print("Update!")
        return successful_result(method=action.method, info="")
template = Template()

(synctree.source > synctree.destination) | template
```

    Update!



```python

```
