from synctree import SyncTree

synctree = SyncTree(['source', 'destination'], ['students', 'staff', 'classes', 'enrollments'])
synctree.show()

synctree.new('source', 'students', '111', name='NoName', grade=7)
synctree.new('destination', 'students', '111', name='NoName', grade=6)

synctree.show()
synctree.show('students', '111')

for item in synctree.source - synctree.destination:
	print(item)

from synctree.templates import DefaultTemplate
from synctree.results import successful_result

class Template(DefaultTemplate):
	def update_students_grade(self, action):
		print("Updated!")
		return successful_result(method=action.method, info="")
template = Template()

# Manual dispatcher:
for action_item in synctree.source - synctree.destination:
	method = getattr(template, action_item.method)
	method(action_item)

# Automatic dispatching:
(synctree.source > synctree.destination) | template

