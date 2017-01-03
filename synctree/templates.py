from synctree.exceptions import TemplateDoesNotImplement
import collections
from synctree.utils import return_unimplemented_action, return_action
from synctree.hijacker import coerce_returns_to_list
import inspect
from synctree.utils import class_string_to_class

class DefaultTemplate:

    _exceptions = '_exceptions delegate success fail not_implemented will_start finished'

    def __init__(self):
        """
        Outfit each member so it coerces
        """
        for prop, method in [(p, m) for p, m in inspect.getmembers(self) if not p.startswith('__') and not p in self._exceptions]:
            setattr(self, prop, coerce_returns_to_list(method))

    def will_start(self):
        pass

    def finished(self):
        pass

    def delegate(self, action, result):
        if result.exception is True:
            self.exception(action, result)
        else:
            if result.success is True:
                self.success(action, result)
            elif result.success is False:
                self.fail(action, result)
            elif result.success is None:
                self.not_implemented(action, result)
            else:
                raise NotImplemented()

    def success(self, action, result):
        pass        

    def fail(self, action, result):
        pass

    def not_implemented(self, action, result):
        """
        Override if this
        """
        raise TemplateDoesNotImplement("{0.__class__.__name__} does not implement method {1}".format(self, action.message))

    def exception(self, action, result):
        pass

    def __call__(self, action):
        method_str = action.message
        try:
            method = getattr(self, method_str)
        except AttributeError:
            self.delegate( return_action(message=method_str), return_unimplemented_action(message=action.message) )
            return

        # Get the result, iterate over it if it is an iterable
        # We can expect it to be a list
        returned = method(action)  # assume it is a list, due to coerce...
        for return_item in returned:
            self.delegate(action, return_item)

class PrintTemplate(DefaultTemplate):
    def __call__(self, action):
        self.delegate(action)

    def delegate(self, action):
        print(action.message, action.idnumber)

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
                lambda action: [return_unimplemented_action(message="Not implementing {}".format(action.message))]  # 
            )

    @property
    def template(self):
        return self._template
