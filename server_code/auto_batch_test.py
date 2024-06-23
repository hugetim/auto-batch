from . import auto_batch as tables
from . import test


@tables.in_transaction
def auto_batch_test():
  test.normal_test_code(tables)
