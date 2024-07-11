import anvil.tables
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
    new_rows = [tables.app_tables.table_2.add_row(text="5") for i in range(10)]
    print(new_rows[0].get_id())
    new_rows[-1].update(text="6")
    print(len(tables.app_tables.table_1.search(row=tables.query.not_(tables.query.not_(rows[1])), rows=tables.query.any_of(row1['rows']))))
    # print(row1._id, row1._table_id, row1._row._id, row1._row._table_id)
    # print(isinstance(row1, tables.Row))
    # print(row1._row == row1)
    # print(row1._id == row1._row._id and row1._table_id == row1._row._table_id)

@anvil.tables.in_transaction
def normal_test():
    normal_test_code(anvil.tables)

@anvil.tables.in_transaction
def batch_test():
    batch_test_code(anvil.tables)
    
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
    new_rows = tables.app_tables.table_2.add_rows([dict(text="5")]*10)
    print(new_rows[0].get_id())
    new_rows[-1].update(text="6")
    print(len(tables.app_tables.table_1.search(row=tables.query.not_(tables.query.not_(rows[1])), rows=tables.query.any_of(row1['rows']))))
