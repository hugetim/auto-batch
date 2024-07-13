import anvil.server
from anvil_extras.server_utils import timed
from . import test
from . import test_auto_batch
from . import test_setup
from . import users
from .tables import app_tables


@anvil.server.callable
def run_tests():
  u = app_tables.users.get(email="poptibo@yahoo.com")
  users.force_login(u)
  batch_user = users.get_user()
  print(u == batch_user)
  for i in range(1):
    test_setup.reset_tables()
    normal_test()
    test_setup.reset_tables()
    batch_test()
    test_setup.reset_tables()
    auto_batch_test()
    test_setup.reset_tables()
    auto_batch_batch_test()

@timed
def normal_test():
  # print("normal_test")
  test.normal_test()


@timed
def batch_test():
  # print("batch_test")
  test.batch_test()


@timed
def auto_batch_test():
  # print("auto_batch_test")
  test_auto_batch.auto_batch_test()

@timed
def auto_batch_batch_test():
  # print("auto_batch_test")
  test_auto_batch.auto_batch_batch_test()
