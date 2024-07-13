import anvil.tables.query
from ..auto_batch import debatchify_inputs


def __getattr__(attr):
    if attr in ('all_of', 'any_of', 'none_of', 'not_'):
        return batch_row_handling(getattr(anvil.tables.query, attr))
    else:
        return getattr(anvil.tables.query, attr)


def batch_row_handling(cls):
    cls.__init__ = debatchify_inputs(cls.__init__)
    return cls
