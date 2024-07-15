from ..auto_batch import USE_WRAPPED, AutoBatch, BatchRow, BatchSearchIterator, BatchTable


WRAPPED_ATTRS = [
    'query',
    'batch_update',
    'batch_delete',
    'Transaction',
    'in_transaction',
    'app_tables',
    'get_table_by_id',
]


def __getattr__(attr):
    if USE_WRAPPED and attr in WRAPPED_ATTRS:
        from . import _tables
        return getattr(_tables, attr)
    else:
        import anvil.tables
        return getattr(anvil.tables, attr)
