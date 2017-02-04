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

This creates an object in the tree in both the source and the destination. This emulates a situation where a student has gone from grade 6 into grade 7, but the destination (a database, whatever) has not been updated with this information yet. The package does have a means to read in information from CSVs, databases, but for the sake of explanation these manual calls give us the gist.

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

We can also use ```SyncTree.show``` to inspect the actual objects created:

```python
synctree.show('students', '111')
```

Output:

```
source/students/111:
{"name": "NoName", "grade": 7, "idnumber": "111"}

destination/students/111:
{"name": "NoName", "grade": 6, "idnumber": "111"}
```

Synctree knows how to discover the differences in attributes (in our case, the change in grade), and reports it:

```python
list(synctree.source - synctree.destination)  # operator overload indicates "find the difference"
```

Output:

```
[Action(idnumber='111', obj=<synctree.utils.SourceStudents object at 0x1017661d8>, source=<synctree.utils.SourceStudents object at 0x1017661d8>, dest=<synctree.utils.DestinationStudents object at 0x1017662c8>, method='update_students_grade', attribute='grade', value=7, old_value=6)]
```

Notice that Synctree has identified the values that have changed, and created a string "update_students_grade" which we can use to operate upon. Let's make a class with a method that corresponds to that string:

```python
from synctree.templates import DefaultTemplate
class Template(DefaultTemplate):
    def update_students_grade(self, action):
        print("Update!")
```

By creating a class with the method ```Template.update_students_grade```, we can use a simple dispatcher to flow our control that way.

```python
for action_item in synctree.source - synctree.destination:
        method = getattr(template, action_item.method)
        method(action_item)
# Output: "Update!"
```

We can automate this by refining our template's method to return a ```Template.successful_result```, which gives us the ability to use more operator overloads to handle the dispatch for us:

```python
from synctree.templates import DefaultTemplate
class Template(DefaultTemplate):
    def update_students_grade(self, action):
        print("Update!")
        return self.successful_result(method=action.method, info="")
        
(synctree.source > synctree.destination) | template

# Output: "Update!"
```
