import anvil.tables.query
from ..auto_batch import USE_WRAPPED


def batch_row_handling(cls):
    from ..auto_batch import debatchify_inputs
    cls.__init__ = debatchify_inputs(cls.__init__)
    return cls


def __getattr__(attr):
    if USE_WRAPPED and attr in ('all_of', 'any_of', 'none_of', 'not_'):
        return batch_row_handling(getattr(anvil.tables.query, attr))
    else:
        return getattr(anvil.tables.query, attr)
