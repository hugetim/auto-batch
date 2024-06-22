import anvil.server
from anvil.tables import app_tables
import anvil.tables
from uuid import uuid4
from time import sleep


write_attempts = 0
rows = app_tables.table_2.search()


@anvil.server.callable
def write_id_to_table():
  this_id = uuid4()
  print(this_id)
  write_to_table(this_id)
  
  
@anvil.tables.in_transaction
def write_to_table(this_id):
  rows = app_tables.table_1.search()
  wrapped_row = ProposalTime(rows[0])
  wrapped_row.add(this_id)
  sleep(.5)
  global write_attempts
  write_attempts += 1
  print(write_attempts)
  if write_attempts < 2:
    raise anvil.tables.TransactionConflict()

    
class ProposalTime():
  
  def __init__(self, proptime_row):
    self._proptime_row = proptime_row

  def get_id(self):
    return self._proptime_row.get_id()  
  
  @property
  def _row(self):
    return self._proptime_row

  def __getitem__(self, key):
    return self._proptime_row[key]

  def __setitem__(self, key, value):
    self._proptime_row[key] = value
  
  def add(self, this_id):
    self['object'] += [str(this_id)[:10]]
    self['rows'] += [rows[0]]
    