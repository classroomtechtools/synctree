"""
Class and method decorator that hijacks all methods (with exceptions)
Enables the ability for a class to choose to either return an object
or else a list of objects

If just an object, returns [obj]
This way other code can depend on it being a list of things that are being returned
"""

import collections, inspect

class coerce_returns_to_list:
	"""
	Decorator pattern class that converts any returns from function into a list
	"""

	def __init__(self, method):
		self.method = method

	def __call__(self, *args, **kwargs):
		"""
		coerces by using a dictionary:
		TODO: What if it is a subclass of list?
		"""
		try:
			result = self.method(*args, **kwargs)
		except Exception as e:
			from synctree.utils import return_exception   # FIXME: Reorg so I don't have to do this
			return [ return_exception(sentline=args[0].message + ': ' + args[0].idnumber, message=e) ]
		return result if type(result) == type([]) else [result]
