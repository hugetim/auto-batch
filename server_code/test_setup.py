from anvil.tables import app_tables
import anvil.tables as tables


DATA = [dict(text="1")]*5


def reset_tables():
  app_tables.table_2.delete_all_rows()
  app_tables.table_2.add_rows(DATA)
