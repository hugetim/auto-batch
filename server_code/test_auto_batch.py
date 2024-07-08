from . import tables
from . import test


@tables.in_transaction
def auto_batch_test():
  test.normal_test_code(tables)

@tables.in_transaction
def auto_batch_batch_test():
  test.batch_test_code(tables)
