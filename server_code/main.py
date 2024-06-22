import anvil.server
from anvil_extras.server_utils import timed
import test
import test_setup


@anvil.server.callable
def run_tests():
  test_setup.reset_tables()
  normal_test()
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
  # monkey patch tables
  test.normal_test_code()


