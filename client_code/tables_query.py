import anvil.tables.query
from .auto_batch import debatchify


def __getattr__(attr):
    if attr in ('all_of', 'any_of', 'none_of', 'not_'):
        return batch_row_handling(getattr(anvil.tables.query, attr))
    else:
        return getattr(anvil.tables.query, attr)


def batch_row_handling(cls):
    original_init = cls.__init__

    def new_init(self, *query_expressions):
        debatchified_exps = [debatchify(exp) for exp in query_expressions]
        return original_init(self, *debatchified_exps)

    cls.__init__ = new_init
    return cls
