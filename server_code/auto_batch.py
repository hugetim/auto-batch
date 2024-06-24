import anvil.tables
from anvil.tables import Row, SearchIterator, Table
from functools import wraps
from collections import defaultdict


def __getattr__(attr):
    return getattr(anvil.tables, attr)


_batch_tables = {}
_update_queue = defaultdict(dict)  # Queue for update operations
_batching = False
_TABLE_NAMES = {anvil.tables.app_tables[name]._id: name for name in list(anvil.tables.app_tables)}


class AutoBatch:
  def __enter__(self):
    # init. caching, clearing any prev. cache
    global _batching
    self.clear()
    _batching = True
    
  def __exit__(self, exc_type, exc_value, exc_tb):
    # execute cached actions and exit
    global _batching
    process_batch()
    _batching = False
    self.clear()

  def clear(self):
      global _batch_tables
      for batch_table in _batch_tables.values():
          batch_table.clear_cache()
      _batch_tables.clear()


def process_batch():
    global _update_queue
    with anvil.tables.batch_update:
        for row, fields in _update_queue.items():
            row.update(**fields)
    _update_queue.clear()


class BatchRow(Row):
    def __init__(self, row):
        self.row = row
        # self._column_types = {col['name']: col['type'] for }
        self._cache = {}

    def __getitem__(self, column):
        if column in self._cache:
            item = self._cache[column]
        else:
            item = self._process_item(self.row[column])
            if _batching:
                self._cache[column] = item
        return item

    def _process_item(self, item):
        if isinstance(item, anvil.tables.Row):
            batch_table = _batch_tables[_TABLE_NAMES[item._table_id]]
            return batch_table.get_batch_row(item)
        elif isinstance(item, list) and item and isinstance(item[0], anvil.tables.Row):
            batch_table = _batch_tables[_TABLE_NAMES[item[0]._table_id]]
            return [batch_table.get_batch_row(row) for row in item]
        else:
            return item
    
    def update(self, **fields):
        if _batching:
            if self.row not in _update_queue:
                _update_queue[self.row] = {}
            _update_queue[self.row].update(fields)
            self._cache.update(fields)
        else:
            self.row.update(**fields)

    def delete(self):
        raise NotImplementedError
  
    def get_id(self):
        return self.row.get_id()
  
    def __len__(self):
        return len(self.row)


class BatchSearchIterator(SearchIterator):
    def __init__(self, batch_table, search_iterator):
        self.batch_table = batch_table
        self.search_iterator = search_iterator
  
    def __len__(self):
        return len(self.search_iterator)

    def __iter__(self):
        for row in iter(self.search_iterator):
            yield self.batch_table.get_batch_row(row)

    def __getitem__(self, index):
        row = self.search_iterator[index]
        return self.batch_table.get_batch_row(row)


class BatchTable(Table):
    def __init__(self, table_name):
        self.table_name = table_name
        self.table = anvil.tables.app_tables[self.table_name]
        self.clear_cache()

    def search(self, *args, **kwargs):
        return BatchSearchIterator(self, self.table.search(*args, **kwargs))

    def get(self, *args, **kwargs):
        return self.get_batch_row(self.table.get(*args, **kwargs))
    
    def get_batch_row(self, row):
        if row.get_id() in self._cache:
            batch_row = self._cache[row.get_id()]
        else:
            batch_row = BatchRow(row)
            if _batching:
                self._cache[row.get_id()] = batch_row
        return batch_row

    def get_by_id(self, row_id):
        if row_id in self._cache:
            batch_row = self._cache[row_id]
        else:
            batch_row = self.get_batch_row(self.table.get_by_id(row_id))
        return batch_row
    
    def clear_cache(self):
        self._cache = {}


class AppTables:
    def __getattr__(self, table_name):
        return self[table_name]

    def __getitem__(self, table_name):
        global _batch_tables
        if table_name in _batch_tables:
            batch_table = _batch_tables[table_name]
        else:
            batch_table = BatchTable(table_name)
            if _batching:
                _batch_tables[table_name] = batch_table
        return batch_table


app_tables = AppTables()


# class DataTableCache:
#     def __init__(self):
#         self.cache = defaultdict(dict)  # Cache for table rows
#         self.add_queue = defaultdict(list)  # Queue for add_row operations
#         self.delete_queue = defaultdict(list)  # Queue for delete operations
#         self.update_queue = defaultdict(dict)  # Queue for update operations
#         self.in_transaction = False

#     def start_transaction(self):
#         self.in_transaction = True

#     def commit_transaction(self):
#         if not self.in_transaction:
#             return
        
#         # Perform all batched add operations
#         for table_name, rows in self.add_queue.items():
#             for row in rows:
#                 app_tables[table_name].add_row(**row)
        
#         # Perform all batched delete operations
#         for table_name, row_ids in self.delete_queue.items():
#             for row_id in row_ids:
#                 row = app_tables[table_name].get_by_id(row_id)
#                 if row is not None:
#                     row.delete()
        
#         # Perform all batched update operations
#         for table_name, updates in self.update_queue.items():
#             for row_id, fields in updates.items():
#                 row = app_tables[table_name].get_by_id(row_id)
#                 if row is not None:
#                     row.update(**fields)
        
#         # Clear all caches and queues
#         self.cache.clear()
#         self.add_queue.clear()
#         self.delete_queue.clear()
#         self.update_queue.clear()
#         self.in_transaction = False

#     def rollback_transaction(self):
#         # Clear all caches and queues without applying changes
#         self.cache.clear()
#         self.add_queue.clear()
#         self.delete_queue.clear()
#         self.update_queue.clear()
#         self.in_transaction = False

#     def get(self, table_name, **query):
#         if self.in_transaction:
#             # Use cache if available
#             key = frozenset(query.items())
#             if key in self.cache[table_name]:
#                 return self.cache[table_name][key]
#             else:
#                 # Otherwise query the database and store in cache
#                 row = app_tables[table_name].get(**query)
#                 self.cache[table_name][key] = row
#                 return row
#         else:
#             return app_tables[table_name].get(**query)

#     def get_by_id(self, table_name, row_id):
#         if self.in_transaction:
#             if row_id in self.cache[table_name]:
#                 return self.cache[table_name][row_id]
#             else:
#                 row = app_tables[table_name].get_by_id(row_id)
#                 self.cache[table_name][row_id] = row
#                 return row
#         else:
#             return app_tables[table_name].get_by_id(row_id)

#     def add_row(self, table_name, **fields):
#         if self.in_transaction:
#             self.add_queue[table_name].append(fields)
#         else:
#             app_tables[table_name].add_row(**fields)

#     def delete(self, table_name, row_id):
#         if self.in_transaction:
#             self.delete_queue[table_name].append(row_id)
#         else:
#             row = app_tables[table_name].get_by_id(row_id)
#             if row is not None:
#                 row.delete()

#     def update(self, table_name, row_id, **fields):
#         if self.in_transaction:
#             if row_id not in self.update_queue[table_name]:
#                 self.update_queue[table_name][row_id] = {}
#             self.update_queue[table_name][row_id].update(fields)
#         else:
#             row = app_tables[table_name].get_by_id(row_id)
#             if row is not None:
#                 row.update(**fields)

# # Example Usage
# cache = DataTableCache()
# cache.start_transaction()

# # Perform some operations
# row = cache.get('my_table', name='example')
# if row:
#     cache.update('my_table', row.get_id(), value=456)
# cache.add_row('my_table', name='new_row', value=123)
# cache.delete('my_table', row.get_id())

# # Commit the transaction
# cache.commit_transaction()

def in_transaction(*d_args, **d_kwargs):
    only_arg_is_func_to_decorate = (len(d_args) == 1 and callable(d_args[0]) and not d_kwargs)
    if only_arg_is_func_to_decorate:
        func_to_decorate = d_args[0]
        tables_in_transaction = anvil.tables.in_transaction
    else:
        tables_in_transaction = anvil.tables.in_transaction(*d_args, **d_kwargs)
    
    def decorator(func):
        
        @tables_in_transaction
        @wraps(func)
        def out_function(*args, **kwargs):
            with AutoBatch():
              result = func(*args, **kwargs) # Call the original function
            return result
        
        return out_function
    
    # Return the decorator function if called with decorator args
    if only_arg_is_func_to_decorate:
        return decorator(func_to_decorate)
    else:
        return decorator
