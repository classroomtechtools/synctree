from synctree.exceptions import TemplateDoesNotImplement
import collections
from synctree.actions import define_action
from synctree.results import exception_during_call, dropped_action
from synctree.hijacker import coerce_returns_to_list
import inspect
from synctree.utils import class_string_to_class
from collections import defaultdict, namedtuple


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
        pass


class DefaultTemplate:

    _exceptions = 'init reporter will_start finished successful_result unsucessful_result dropped_action exception_during_call'
    _reporter = Reporter

    def __init__(self):
        """
        Outfit each member so it coerces
        """
        for prop, method in [(p, m) for p, m in inspect.getmembers(self) if not p.startswith('_') and p not in self._exceptions]:
            setattr(self, prop, coerce_returns_to_list(method))
        self.init()

    def init(self):
        self.reporter = self._reporter()

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
    """
    A template that automatically drops all calls to it.
    In settings.ini, using :off after subbranch enables this particular class
    """
    def __init__(self, template, mock=False, only_these=None, exclude_these=None):

        template_klass = class_string_to_class(template)
        template_klass._mock = mock
        self._template = template_klass()

        if only_these:
            identified = [v for v in vars(self._template).keys() if v not in self._template._exceptions and v not in only_these.split(' ')]
        elif exclude_these:
            identified = [v for v in vars(self._template).keys() if v not in self._template._exceptions and v in exclude_these.split(' ')]

        for attr in identified:
            # If inside this lambda an exception is raised at runtime we'll have undefined behaviour:
            setattr(self._template, attr,
                lambda action: [dropped_action(method="unimpl: {}".format(action.method))]
            )

    @property
    def template(self):
        return self._template


class LoggerReporter:
    """
    Keep records of everything that has been done
    """
    _log = defaultdict(lambda: defaultdict(list))

    def append_this(self, action, obj):
        self._log[action.obj.__subbranch__][action.idnumber].append(obj)

    def exception(self, action, result):
        self._log[action.obj.__subbranch__][action.idnumber].append((action, result))

    def success(self, action, result):
        self._log[action.obj.__subbranch__][action.idnumber].append((action, result))

    def fail(self, action, result):
        self._log[action.obj.__subbranch__][action.idnumber].append((action, result))

    def will_start(self):
        pass

    def finished(self):
        pass

    def not_implemented(self, action, result):
        """
        Override if this
        """
        # FIXME: Where to store the context info?
        self._log['unimplemented'][result.method].append(result)


class LoggerTemplate(DefaultTemplate):
    """
    """
    _reporter = LoggerReporter
