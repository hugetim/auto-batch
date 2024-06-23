import anvil.tables as tables
from anvil_extras.logging import TimerLogger


def normal_test_code(tables):
  with TimerLogger("normal_test_code", format="{name}: {elapsed:6.3f} s | {msg}") as timer:
    rows = tables.app_tables.table_2.search()
    timer.check("search")
    len(rows)
    timer.check("len(search result)")
    for row in rows:
      row.update(text="2")


@tables.in_transaction
def normal_test():
  normal_test_code(tables)

@tables.in_transaction
def batch_test_code():
  with TimerLogger("batch_test_code", format="{name}: {elapsed:6.3f} s | {msg}") as timer:
    rows = tables.app_tables.table_2.search()
    timer.check("search")
    len(rows)
    timer.check("len(search result)")
    with tables.batch_update:
      for row in rows:
        row.update(text="2")
