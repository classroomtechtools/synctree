# synctree
Framework for importing / exporting information between CSVs and databases

###QUICKSTART

The framework is initialized with the creation of a tree structure, which has `branches` and `subbranches`. The idea is that the branches represent data points, such as sources or destinations, and the subbranches represent the kinds of objects that are to be synced (in the model).

```python
from synctree import SyncTree
synctree = SyncTree(['source', 'destination'], ['students', 'staff', 'classes', 'enrollments'])

synctree.show()
```

Output:

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
```

Notice that the tree is mirrored: Both branches have the same number of subbranches. Leaves of each subbranch, which can be manually creaeted with `SyncTree.new` represent objects in a model:

```python
synctree.new('source', 'students', '111', name="NoName" grade=7)
synctree.new('destination', 'students', '111', name="NoName" grade=6)
```

This creates a record in the tree where a sync operation is required, as it appears that the student has gone into grade 7, whereas the destination has not been updated with this information yet.

```python
synctree.show()
```

Output:

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
```

Synctree knows how to discover attribute differences, and reports it:

```python
list(synctree.source - synctree.destination)  # operator overload indicates "find the difference"
```

This creates a students on the destination branch, one which is entirely identical to the source. Notice that `999` does not exist in the destination, and needs to be synced over.

```python
[Action(idnumber='111', obj=<synctree.utils.SourceStudents object at 0x103b35048>, source=<synctree.utils.SourceStudents object at 0x103b35048>, dest=<synctree.utils.DestinationStudents object at 0x103b35138>, method='update_students_grade', attribute='grade', value=7, old_value=6)]
```

Notice that Synctree has identified the values that have changed, and created a named method `update_students_grade` which we can use to operate upon. Let's make a class with that method:

```python
from synctree.templates import DefaultTemplate
class Template(DefaultTemplate):
    def update_students_grade(self, action):
        print("Update!")
```

In order to actually do anything, you have to define a template, by creating a class whose method ```new_students``` connects to the database or whatever action occurs when a new student arrives at the school.

```python
from synctree.templates import DefaultTemplate

class Template(DefaultTemplate):
        def update_students_grade(self, action):
                print("Update!")
template = Template()
```

Then we can loop through:

```python
for action_item in synctree.source - synctree.destination:
        method = getattr(template, action_item.method)
        method(action_item)
# Output: "Update!"
```

Or we can use this instead:

```python
(synctree.source > synctree.destination) | template
```
