from . import query
from ..auto_batch import batch_tables as app_tables
from ..auto_batch import get_table_by_id, AutoBatch, BatchRow, BatchSearchIterator, BatchTable
import anvil.tables
from functools import wraps
#from contextlib import nullcontext


class _NullContext: # b/c Skulpt lacks contextlib
    def __enter__(self):
        return None
    
    def __exit__(self, exc_type, exc_value, traceback):
        return False


def __getattr__(attr):
    return getattr(anvil.tables, attr)


batch_update = _NullContext()
batch_delete = _NullContext()


class Transaction:
    def __init__(self, *args, **kwargs):
        self.transaction = anvil.tables.Transaction(*args, **kwargs)
        self.auto_batch = AutoBatch()

    def __enter__(self):
        txn = self.transaction.__enter__()
        self.auto_batch.__enter__()
        return txn

    def __exit__(self, exc_type, exc_value, traceback):
        self.auto_batch.__exit__(exc_type, exc_value, traceback)
        return self.transaction.__exit__(exc_type, exc_value, traceback)

    def abort(self):
        self.transaction.abort()


def in_transaction(*d_args, **d_kwargs):
    # added complications due to @in_transaction's optional 'relaxed' argument:
    only_arg_is_func_to_decorate = (len(d_args) == 1 and callable(d_args[0]) and not d_kwargs)
    if only_arg_is_func_to_decorate:
        func_to_decorate = d_args[0]
        tables_in_transaction = anvil.tables.in_transaction
    else: #decorator was specified with arg(s) (i.e. 'relaxed')
        # func-to-decorate not known yet
        tables_in_transaction = anvil.tables.in_transaction(*d_args, **d_kwargs)
    
    def in_transaction_with_auto_batch(func):
        @tables_in_transaction
        @wraps(func)
        def out_function(*args, **kwargs):
            with AutoBatch():
              result = func(*args, **kwargs) # Call the original function
            return result
        return out_function
    
    if only_arg_is_func_to_decorate:
        return in_transaction_with_auto_batch(func_to_decorate)
    else: # composite decorator now configured for 'relaxed' transaction
        # Return composite decorator as a function, to then be applied to func-to-decorate
        return in_transaction_with_auto_batch
