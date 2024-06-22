import anvil.tables as tables
from functools import wraps
from collections import defaultdict


_cache = defaultdict(dict)  # Cache for tables
_batch_rows = defaultdict(dict)
_update_queue = defaultdict(dict)  # Queue for update operations
_in_transaction = False


class AutoBatch:
  def __enter__(self):
    # init. caching, clearing any prev. cache
    global _in_transaction
    self.clear()
    _in_transaction = True
    
  def __exit__(self, exc_type, exc_value, exc_tb):
    # execute cached actions and exit
    global _in_transaction
    _execute_queue()
    _in_transaction = False
    self.clear()

  def clear(self):
    global _cache, _batch_rows, _update_queue
    # _cache.clear()
    # _batch_rows.clear()
    _update_queue.clear()



def _execute_queue():
    with tables.batch_update:
        for row, fields in _update_queue.items():
            row.update(**fields)


class BatchRow:
    def __init__(self, row):
        # global _cache, _batch_rows
        self.row = row
        # self.id = row.get_id()
        # _cache[self.id] = dict(row)  #TODO: both _cache and _batch_rows need to be like [table_name][row_id]
        # _batch_rows[self.id] = self

    def update(self, **fields):
        if _in_transaction:
            if self.row not in _update_queue:
                _update_queue[self.row] = {}
            _update_queue[self.row].update(fields)
            _cache[self.id].update(fields)
        else:
            self.row.update(**fields)
    

class BatchTable:
    def __init__(self, table_name):
        self.table = tables.app_tables[table_name]

    def search(self, *args, **kwargs):
        for row in self.table.search(*args, **kwargs):
            yield BatchRow(row)


class AppTables:
    def __getattr__(self, table_name):
        return BatchTable(table_name)


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
        tables_in_transaction = tables.in_transaction
    else:
        tables_in_transaction = tables.in_transaction(*d_args, **d_kwargs)
    
    def decorator(func):
        @wraps(func)
        @tables_in_transaction
        def out_function(*args, **kwargs):
            with AutoBatch:
              result = func(*args, **kwargs) # Call the original function
            return result
        
        return out_function
    
    # Return the decorator function if called with decorator args
    if only_arg_is_func_to_decorate:
        return decorator(func_to_decorate)
    else:
        return decorator
