import importlib, inspect
from collections import namedtuple
import json


class initobj:
	"""
	Light wrapper object that follows model object creation steps
	Used so that we can use consistent API for naked objects	
	"""
	def __init__(self, branch, subbranch, **kwargs):
		self._klass_name = f'{branch.title()}{subbranch.title()}'

    def default(self, obj):
        if isinstance(obj, Branch):
            return obj.to_json()
        elif isinstance(obj, SubBranch):
            return obj.to_json()
        elif isinstance(obj, Base):
            # All base objects become properties
            return obj._to_json
        return super().encode(self, obj)


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


def extend_template_exceptions(more_exceptions: '', klass=None):
	"""
	Templates need to define exceptions which are not actual template methods

	Usage:
	class MyTemplate(DefaultTemplate):
		extend_template_exceptions('more')

		def more(self):
			pass  # do something that is not template-like
	"""
	if klass is None:
		from synctree.templates import DefaultTemplate
		klass = DefaultTemplate
	return f"{klass._exceptions} {more_exceptions}"


def class_string_to_class(passed_string: 'module.submodule.ClassName'):
	"""
	Get class object from string specification

	Usage:
	klass = class_string_to_class('importable.path.to.Klass')
	object = klass()
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


