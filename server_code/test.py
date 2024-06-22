from anvil.tables import app_tables
import anvil.tables as tables


@tables.in_transaction
def normal_test_code():
  rows = app_tables.table_2.search()
  for row in rows:
    row.update(text="2")


@tables.in_transaction
def batch_test_code():
  rows = app_tables.table_2.search()
  with tables.batch_update:
    for row in rows:
      row.update(text="2")
