import importlib, inspect
from collections import namedtuple

Action = namedtuple('Action', 'idnumber source dest message attribute value old_value')
ActionResult = namedtuple('ActionResult', 'success message sentline exception')

def return_action(**kwargs):
    for key in set(Action._fields) - set(kwargs):
        kwargs[key] = None
    return Action(**kwargs)

def return_successful_result(message="<no message>", sentline=None):
	return ActionResult(success=True, message=message, sentline=sentline, exception=False)

def return_unsuccessful_result(message="<no message>", sentline=""):
	return ActionResult(success=False, message=message, sentline=sentline, exception=False)

def return_unimplemented_action(message="<no message>", sentline=None):
	return ActionResult(success=None, message=message, sentline=sentline, exception=False)

def return_ignored_action():
	return ActionResult(success=None, message=None, sentline=None, exception=False)

def return_exception(sentline="", message=""):
	return ActionResult(success=False, message=message, sentline=sentline, exception=True)

def cascading_result(method_calls_tuple_list):
	"""
	When passed a list of method calls with the accompanying arguments,
	Call them until we got an unsuccessful result
	or until all of them have been exhausted
	"""
	ret = []
	for method, *args in method_calls_tuple_list:
		results = method(*args)
		for r in results:
			ret.append(r)
			if r.success is False:
				return ret
	return ret

def extend_template_exceptions(more_exceptions, klass=None):
	if klass is None:
		from synctree.templates import DefaultTemplate
		klass = DefaultTemplate
	return DefaultTemplate._exceptions + ' ' + more_exceptions

def class_string_to_class(passed_string: 'module.submodule.ClassName'):
	"""
	Get class object from string specification
	"""
	if passed_string is None: return None
	if inspect.isclass(passed_string): return passed_string
	split = passed_string.split('.')
	if len(split) == 1:
		# Support the ability to use synctree.__init__ file to import directly
		# into the app, which is useful for cli 
		# No dot notation has signficiance, this way, and provides a useful feature
		# Fill in root module name, continue:
		split = ['ssis_synctree', *split]
	parent_module, class_name = split[:-1], split[-1]
	try:
		module = importlib.import_module(".".join(parent_module))
	except ValueError:
		raise ImportError("Cannot import module '{}'".format(passed_string))
	return getattr(module, class_name.replace('_', ''))

class Wheel:
	"""
	Provides interface to cycle through templating system
	Using the passed gen_obj on __init__, create instance of template, 
	"""
	def __init__(self, gen_obj):
		self.gen_obj = gen_obj

	def __iter__(self):
		return self.gen_obj()

	def __or__(self, other):  # |
		"""
		Syntax:
		wheel | template
		wheel object is created via > operator on branches
		self is an iterable, calls template.__call__ to execute as necessary
		"""

		# It's possible to be be passed an object at this point

		if isinstance(other, str):
			other = class_string_to_class(other)
			other = other()

		# try:
		# 	if hasattr(other, '_exceptions'):
		# 		exceptions = getattr(other, '_exceptions')
		# 	else:
		# 		exceptions= ''
		# 	other = augment_template(exceptions)(other)
		# except TypeError:
		# 	raise TypeError("Template class or importable string expected")


		if not callable(other):
			raise TypeError("Template class or callable object expected")
		other.will_start()
		for item in self:
			other(item)
		other.finished()

