import anvil.server
from anvil_extras.server_utils import timed
from . import test
from . import test_setup
from . import auto_batch


@anvil.server.callable
def run_tests():
  for i in range(1):
    test_setup.reset_tables()
    normal_test()
    test_setup.reset_tables()
    batch_test()
    test_setup.reset_tables()
    auto_batch_test()


@timed
def normal_test():
  test.normal_test_code()


@timed
def batch_test():
  test.batch_test_code()


@timed
def auto_batch_test():
  test.tables = auto_batch
  test.normal_test_code()


