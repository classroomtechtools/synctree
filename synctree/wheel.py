"""
Provides interface to cycle through templating system
Using the passed gen_obj on __init__, create instance of template
"""

from synctree.utils import class_string_to_class


class Wheel:
	def __init__(self, gen_obj):
		self.gen_obj = gen_obj

	def __iter__(self):
		return self.gen_obj()

	def __or__(self, other):  # |
		"""
		Usage:
		wheel | template
		wheel object is created via > operator on branches
		self is an iterable, calls template.__call__ to execute as necessary
		"""

		# It's possible to be be passed either an object or importable string
		if isinstance(other, str):
			other = class_string_to_class(other)
			other = other()

		if not callable(other):
			raise TypeError("Template class or callable object expected")

		other.reporter.will_start()

		for item in self:
			# route through the template
			other(item)

		other.reporter.finished()
