from . import auto_batch_tables as tables
from . import test


@tables.in_transaction
def auto_batch_test():
  test.normal_test_code(tables)
