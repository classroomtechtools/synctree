from collections import namedtuple
Action = namedtuple('Action', 'idnumber obj source dest method attribute value old_value')


def define_action(**kwargs):
    for key in set(Action._fields) - set(kwargs):
        kwargs[key] = None
    return Action(**kwargs)
