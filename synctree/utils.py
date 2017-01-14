import importlib, inspect

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

def extend_template_exceptions(more_exceptions: '', klass=None):
	if klass is None:
		from synctree.templates import DefaultTemplate
		klass = DefaultTemplate
	return f"{DefaultTemplate._exceptions} {more_exceptions}"

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


