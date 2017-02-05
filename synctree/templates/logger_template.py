from . import DefaultTemplate
from collections import defaultdict


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
    _reporter_class = LoggerReporter