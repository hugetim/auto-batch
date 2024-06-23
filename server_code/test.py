import anvil.tables as tables


def normal_test_code():
  rows = tables.app_tables.table_2.search()
  for row in rows:
    a = {row: 3}
    row.update(text="2")


@tables.in_transaction
def normal_test():
  normal_test_code()

@tables.in_transaction
def batch_test_code():
  rows = tables.app_tables.table_2.search()
  with tables.batch_update:
    for row in rows:
      row.update(text="2")
