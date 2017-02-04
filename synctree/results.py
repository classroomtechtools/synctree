from collections import namedtuple
ActionResult = namedtuple('MethodResult', 'success method info exception')

def successful_result(method="<no method>", info=None):
	return ActionResult(success=True, method=method, info=info, exception=False)

def unsuccessful_result(method="<no method>", info=""):
	return ActionResult(success=False, method=method, info=info, exception=False)

def dropped_action(method):
	""" Dropped actions are those that are purposefully removed as an action, with no effect anywhere """
	return ActionResult(success=None, method=method, info=None, exception=False)

def exception_during_call(method="", info=""):
	""" Indicates that a run-time error occurred while calling the method """
	return ActionResult(success=False, method=method, info=info, exception=True)