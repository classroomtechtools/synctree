"""
Class and method decorator that hijacks all methods (with exceptions)
Enables the ability for a class to choose to either return an object
or else a list of objects

If just an object, returns [obj]
This way other code can depend on it being a list of things that are being returned
"""

import collections, inspect, functools

class coerce_returns_to_list:
	"""
	Decorator pattern class that converts any returns from function into a list
	"""

	def __init__(self, wrapped):
		self.wrapped = wrapped
		functools.update_wrapper(self, wrapped)

	def __call__(self, *args, **kwargs):
		"""
		coerces by using a dictionary:
		TODO: What if it is a subclass of list?
		"""
		try:
			result = self.wrapped(*args, **kwargs)
		except Exception as e:
			from synctree.results import exception_during_call   # FIXME: Reorg so I don't have to import here to avoid circular dependency
			action = args[0]
			sentline = "{0.method}: {0.idnumber}".format(action)
			ret = exception_during_call(info=e, method=sentline)
			return [ret]
		return result if type(result) == type([]) else [result]
