import auto_batch as tables
import test


@tables.in_transaction
def auto_batch_test():
  normal_test_code()
