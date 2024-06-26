import anvil.tables as tables
from anvil_extras.logging import TimerLogger


def normal_test_code(tables):
    with TimerLogger("normal_test_code", format="{name}: {elapsed:6.3f} s | {msg}") as timer:
        rows = tables.app_tables.table_2.search()
    len(rows)
    for row in rows:
        row.update(text="2")
    print(rows[0]['text'])
    tables.app_tables.table_2.get_by_id(rows[0].get_id())
    row1 = tables.app_tables.table_1.get(object="test")
    print(row1['row']['text'])
    print(row1['rows'][0]['text'])
    row1['row']['text'] = "3"
    print(bool(tables.app_tables.table_2.get(text="3")))
    row1.update(rows=[row1['row']])
    row1['row'] = rows[1]
    rows[3].delete()
    try:
        print(rows[3]['text'])
    except tables.RowDeleted as e:
        print(repr(e))


@tables.in_transaction
def normal_test():
    normal_test_code(tables)

@tables.in_transaction
def batch_test():
    batch_test_code(tables)
    
def batch_test_code(tables):
    with TimerLogger("batch_test_code", format="{name}: {elapsed:6.3f} s | {msg}") as timer:
        rows = tables.app_tables.table_2.search()
    len(rows)
    with tables.batch_update:
        for row in rows:
            row.update(text="2")
    print(rows[0]['text'])
    tables.app_tables.table_2.get_by_id(rows[0].get_id())
    row1 = tables.app_tables.table_1.get(object="test")
    print(row1['row']['text'])
    print(row1['rows'][0]['text'])
    row1['row']['text'] = "3"
    print(bool(tables.app_tables.table_2.get(text="3")))
    with tables.batch_update:
        row1.update(rows=[row1['row']])
        row1['row'] = rows[1]
    with tables.batch_delete:
        rows[3].delete()
    try:
        print(rows[3]['text'])
    except tables.RowDeleted as e:
        print(repr(e))

