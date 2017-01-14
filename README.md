# synctree
Framework for importing / exporting information between CSVs and databases

###CONTEXT

You're a school with a few providers in an organization. One of them is the source of truth for things like class enrollments and student data, and another open source tool like Google or Moodle. You want the information to one-way sync so you can manage other things.

Using this framework, you define the model for the source, and the targets(s). The framework takes those two models and finds the differences, sending it on to a template. The template code then does the necessary action to update the database.

###IN A NUTSHELL

The framework is initialized with the creation of a tree structure, which has `branches` and `subbranches`. The idea is that the branches represent data points, either sources or destinations, and the subbranches represent the kinds of objects that are to be synced (in the model).

```python
from synctree import SyncTree
synctree = SyncTree(['source', 'destination'], ['students', 'staff', 'classes', 'enrollments'])

synctree.branches              # ['source', 'destination']
synctree.subbranches           # ['students', 'staff', 'classes', 'enrollments']
synctree.source.students       # <Subbranch students of branch source>
synctree.destination.students  # <Subbranch students of branch destination>
```

Notice that the tree is mirrored: Both branches have the same number of subbranches. There are no sub-subbranches, but there are leaves of the subbranch, which will represent particular objects that are to be synced:

```python
synctree.new('source', 'students', '111')   
synctree.new('source', 'students', '999')
```

This creates a bare-bones student associated with the `source` branch with identifier `111`, as well as a student with the identifier `999` which is a new student. Obviously, you can use a CSV file to populate these objects, but under the hood this is what the framework is doing to populate your branch with the information.

```python
synctree.new('destination', 'students', '111')
```
This creates a students on the destination branch, one which is entirely identical to the source. Notice that `999` does not exist in the destination, and needs to be synced over.

```python
synctree.source > synctree.destination
```

The greater than operator tells the framework to extract the differences, and in this case outputs an generator object that creates a series of action objects:

```python
 Action(idnumber='999', message='new_students')
```

In order to actually do anything, you have to define a template, by creating a class whose method ```new_students``` connects to the database or whatever action occurs when a new student arrives at the school.

```python
from synctree import DefaultTemplate
def Template(DefaultTemplate):
	def new_students(self, action):
		pass   # do database action
```

All you need to do is define the importable string for that template, and do like this:

```python
(synctree.source > synctree.destination) | Template
```

Which basically says "Take the differences between the source and destination, and invoke the commands that are defined in an instance of the class".
