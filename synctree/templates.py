from synctree.exceptions import TemplateDoesNotImplement
import collections
from synctree.actions import define_action
from synctree.results import exception_during_call, dropped_action
from synctree.hijacker import coerce_returns_to_list
import inspect
from synctree.utils import class_string_to_class

class Reporter:

    def __init__(self):
        pass

    def exception(self, action, result):
        pass

    def success(self, action, result):
        pass

    def fail(self, action, result):
        pass

    def will_start(self):
        pass

    def finished(self):
        pass

    def not_implemented(self, action, result):
        """
        Override if this
        """
        raise TemplateDoesNotImplement(f"{self.__class__.__name__} does not implement method {action.method}")

class DefaultTemplate:

    _exceptions = 'reporter will_start finished'
    _reporter_class = Reporter

    def __init__(self):
        """
        Outfit each member so it coerces
        """
        for prop, method in [(p, m) for p, m in inspect.getmembers(self) if not p.startswith('_') and not p in self._exceptions]:
            setattr(self, prop, coerce_returns_to_list(method))
        self.reporter = self._reporter_class()


    def __call__(self, action):
        """ Route the call according to action, receive the result and pass to self.reporter """
        try:
            method_to_be_called = getattr(self, action.method)
        except AttributeError:
            action = define_action(method=action.method)
            result = dropped_action(method=action.method)
            self.reporter.not_implemented(action, result)
        else:
            # Get the result, iterate over it if it is an iterable
            # We can expect it to be a list
            for return_item in method_to_be_called(action):
                if return_item.exception is True:
                    self.reporter.exception(action, return_item)
                else:
                    if return_item.success is True:
                        self.reporter.success(action, return_item)
                    elif return_item.success is False:
                        self.reporter.fail(action, return_item)
                    elif return_item.success is None:
                        self.reporter.not_implemented(action, return_item)
                    else:
                        raise NotImplemented()


class PrintTemplate(DefaultTemplate):
    def __call__(self, action):
        self.delegate(action)

    def delegate(self, action):
        print(action.method, action.idnumber)

    def update_courses_name(self, action):
        print("Doing it! But don't let me")

    def old_courses(self, action):
        print(" Doing it but don't let me!")

class BlockedTemplateWrapper:

    def __init__(self, template, only_these=None, exclude_these=None):

        self._template = class_string_to_class(template)()

        if only_these:
            identified = [v for v in vars(self._template).keys() if not v in self._template._exceptions and not v in only_these.split(' ')]
        elif exclude_these:
            identified = [v for v in vars(self._template).keys() if not v in self._template._exceptions and v in exclude_these.split(' ')]

        for attr in identified:
            # If inside this lambda an exception is raised at runtime we'll have undefined behaviour:
            setattr(self._template, attr, 
                lambda action: [dropped_action(method="unimpl: {}".format(action.method))]  # 
            )

    @property
    def template(self):
        return self._template
