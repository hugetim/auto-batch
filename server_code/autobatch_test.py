import auto_batch as tables


@tables.in_transaction
def normal_test_code():
  rows = tables.app_tables.table_2.search()
  for row in rows:
    a = {row: 3}
    row.update(text="2")
