from anvil.tables import app_tables
import anvil.tables as tables


DATA = [dict(text="1")]*60


def reset_tables():
    app_tables.table_2.delete_all_rows()
    new_rows = app_tables.table_2.add_rows(DATA)
    app_tables.table_1.delete_all_rows()
    app_tables.table_1.add_row(object="test", rows=new_rows[0:2])
