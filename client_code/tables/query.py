import anvil.tables.query
from ..auto_batch import debatchify
from functools import wraps


def __getattr__(attr):
    if attr in ('all_of', 'any_of', 'none_of', 'not_'):
        return batch_row_handling(getattr(anvil.tables.query, attr))
    else:
        return getattr(anvil.tables.query, attr)


def batch_row_handling(cls):
    original_init = cls.__init__

    @wraps(original_init)
    def new_init(self, *args, **kwargs):
        debatchified_args = [debatchify(arg) for arg in args]
        debatchified_kwargs = {column: debatchify(value) for column, value in kwargs.items()}
        return original_init(self, *debatchified_args, **debatchified_kwargs)

    cls.__init__ = new_init
    return cls
