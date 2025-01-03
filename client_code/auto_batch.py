import anvil.tables
from anvil.server import portable_class
from collections import defaultdict
from functools import wraps


USE_WRAPPED = True
_add_queue = defaultdict(list)
_update_queue = defaultdict(dict)
_delete_queue = []
_batching = False


def process_batch_add():
    global _add_queue
    for batch_table in _add_queue:
        batch_rows = _add_queue[batch_table]
        column_values_list = [batch_row.cache for batch_row in batch_rows]
        rows = batch_table.table.add_rows(column_values_list)
        for i, row in enumerate(rows):
            batch_rows[i].row = row
    _add_queue.clear()


def process_batch_update():
    global _update_queue
    with anvil.tables.batch_update:
        for batch_row, column_values in _update_queue.items():
            batch_row.row.update(**column_values)
    _update_queue.clear()


def process_batch_delete():
    global _delete_queue
    with anvil.tables.batch_delete:
        for batch_row in _delete_queue:
            batch_row.row.delete()
    _delete_queue.clear()


def process_batch():
    process_batch_add()
    process_batch_update()
    process_batch_delete()


class AutoBatch:
    def __enter__(self):
        global _batching
        self.clear()
        _batching = True
    
    def __exit__(self, exc_type, exc_value, exc_tb):
        global _batching
        process_batch()
        _batching = False
        self.clear()

    def clear(self):
        batch_tables.clear_cache()


def if_not_deleted(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self._deleted:
            raise anvil.tables.RowDeleted("This row has been deleted")
        return func(self, *args, **kwargs)  
    return wrapper


def wrap_row(row):
    if row is None:
        return None
    batch_table = get_table_by_id(row._table_id)
    return batch_table.batch_row(row)


def _wrap_any_rows(value):
    def _is_row_but_not_batch_row(thing):
        return isinstance(thing, anvil.tables.Row) and not isinstance(thing, BatchRow)

    if _is_row_but_not_batch_row(value):
        return wrap_row(value)
    elif isinstance(value, list) and value and _is_row_but_not_batch_row(value[0]):
        return [wrap_row(row) for row in value]
    else:
        return value


def _unwrap_any_rows(value):
    if isinstance(value, BatchRow):
        return value.row
    elif isinstance(value, list) and value and isinstance(value[0], BatchRow):
        return [batch_row.row for batch_row in value]
    else:
        return value


def _unwrap_any_row_values(_dict):
    return {key: _unwrap_any_rows(value) for key, value in _dict.items()}


def unwrap_any_input_rows(func):
    @wraps(func)
    def out_function(*args, **kwargs):
        return func(
            *[_unwrap_any_rows(arg) for arg in args], 
            **_unwrap_any_row_values(kwargs),
        )
    return out_function


@portable_class
class BatchRow(anvil.tables.Row):
    def __init__(self, row):
        self._cache = {} # unwrapped_rows
        self._deleted = False
        self._row = None
        self.row = row # property

    @staticmethod
    def from_batched_add(column_values, batch_table):
        batch_row = BatchRow(None)
        batch_row._cache = column_values
        batch_row.batch_table = batch_table
        return batch_row
    
    @property
    def row(self):
        if not self._row:
            print("AutoBatch: process_batch_add triggered early by BatchRow.row")
            process_batch_add()
        return self._row

    @row.setter
    def row(self, value):
        if self._row:
            raise RuntimeError("BatchRow.row already set")
        if value:
            self._row = value
            get_table_by_id(self._row._table_id).add_batch_row(self)

    @if_not_deleted
    def __eq__(self, other):
        if not isinstance(other, BatchRow):
            return NotImplemented
        if self._row is None:
            return id(other) == id(self)
        return other.row._id == self.row._id and other.row._table_id == self.row._table_id

    @if_not_deleted
    def __hash__(self):
        return hash((self.row._table_id, self.row._id))
    
    @if_not_deleted
    def __getitem__(self, column):
        if column in self._cache:
            return _wrap_any_rows(self._cache[column])
        value = self.row[column]
        if _batching:
            self._cache[column] = value
        return _wrap_any_rows(value)

    @if_not_deleted
    def __setitem__(self, column, value):
        self.update(**{column: value})

    @if_not_deleted
    def update(*args, **column_values):
        global _update_queue
        if len(args) > 2:
            raise TypeError("expected at most 1 argument, got %d" % (len(args) - 1))
        elif len(args) == 2:
            column_values = dict(args[1], **column_values)
        self = args[0]
        if not column_values:
            # backwards compatability hack
            if _add_queue or _update_queue or _delete_queue:
                print("AutoBatch: process_batch triggered early by row.update() w/o args")
            process_batch()
            self.clear_cache()
            return
        unwrapped_column_values = _unwrap_any_row_values(column_values)
        if not _batching:
            return self.row.update(**unwrapped_column_values)
        self._cache.update(unwrapped_column_values)
        if self._row is None:
            return # cache update implicitly updates batch_add, with no need for batch_update then
        _update_queue[self].update(unwrapped_column_values)
        
    @if_not_deleted
    def delete(self):
        global _add_queue, _delete_queue
        self._deleted = True
        if not _batching:
            return self.row.delete()
        if self._row is None:
            return _add_queue[self.batch_table].remove(self)
        _delete_queue.append(self)
            
    @if_not_deleted
    def get_id(self):
        return self.row.get_id()

    @if_not_deleted
    def __repr__(self):
        if self._row is None:
            return f"BatchRow.from_batched_add({repr(self._cache)})"
        return f"BatchRow({repr(self._row)})"          

    @if_not_deleted
    def __str__(self):
        return f"<auto_batch.tables.BatchRow: {self._cache}>"   
    
    @if_not_deleted
    def __iter__(self):
        return iter(dict(self.row).items())

    @if_not_deleted
    def __serialize__(self, global_data):
        if _add_queue or _update_queue or _delete_queue:
            print("AutoBatch: process_batch triggered early by row __serialize__")
        process_batch()
        return self.__dict__
    
    @property
    def cache(self):
        return self._cache
    
    def clear_cache(self):
        self._cache.clear()


@portable_class
class BatchSearchIterator(anvil.tables.SearchIterator):
    def __init__(self, search_iterator):
        self._search_iterator = search_iterator

    def __getitem__(self, index):
        return wrap_row(self._search_iterator[index])
  
    def __len__(self):
        return len(self._search_iterator)

    def __serialize__(self, global_data):
        if _add_queue or _update_queue or _delete_queue:
            print("AutoBatch: process_batch triggered early by search iterator __serialize__")
        process_batch()
        return self.__dict__


@portable_class
class BatchTable(anvil.tables.Table):
    def __init__(self, table):
        self.table = table
        self._batch_rows = {}
        self.clear_cache()
        
    def search(self, *args, **kwargs):
        if _add_queue or _update_queue or _delete_queue:
            print("AutoBatch: process_batch triggered early by search")
        process_batch()
        return BatchSearchIterator(
            unwrap_any_input_rows(self.table.search)(*args, **kwargs)
        )

    def get(self, *args, **kwargs):
        if _add_queue or _update_queue or _delete_queue:
            print("AutoBatch: process_batch triggered early by get")
        process_batch()
        raw_out = unwrap_any_input_rows(self.table.get)(*args, **kwargs)
        return self.batch_row(raw_out) if raw_out else None
    
    def get_by_id(self, row_id, *args, **kwargs):
        if row_id in self._batch_rows:
            return self._batch_rows[row_id]
        else:
            row = self.table.get_by_id(row_id, *args, **kwargs)
            return BatchRow(row)

    def add_row(self, **column_values):
        global _add_queue
        unwrapped_column_values = _unwrap_any_row_values(column_values)
        if not _batching:
            return _wrap_any_rows(self.table.add_row(**unwrapped_column_values))
        batch_row = BatchRow.from_batched_add(unwrapped_column_values, batch_table=self)
        _add_queue[self].append(batch_row)
        return batch_row

    def add_rows(self, column_values_list):
        return [self.add_row(**column_values) for column_values in column_values_list]

    def delete_all_rows(self, *args, **kwargs):
        return self.table.delete_all_rows(*args, **kwargs)

    def add_batch_row(self, batch_row):
        self._batch_rows[batch_row.get_id()] = batch_row
    
    def batch_row(self, row):
        retrieved = self._batch_rows.get(row.get_id())
        return retrieved if retrieved else BatchRow(row)
    
    def __serialize__(self, global_data):
        if _add_queue or _update_queue or _delete_queue:
            print("AutoBatch: process_batch triggered early by table __serialize__")
        process_batch()
        return self.__dict__
    
    def clear_cache(self):
        for batch_row in self._batch_rows.values():
            batch_row.clear_cache()
        #self._batch_rows.clear()


class BatchTables:
    def __init__(self):
        self._name_list = list(anvil.tables.app_tables)
        self._batch_tables = {}
        self._name_lookup = {}
        for name in self._name_list:
            table = anvil.tables.app_tables[name]
            self._batch_tables[name] = BatchTable(table)
            self._name_lookup[table._id] = name
    
    def __getattr__(self, table_name):
        return self[table_name]

    def __getitem__(self, table_name):
        if table_name in self._batch_tables:
            return self._batch_tables[table_name]
        else:
            raise KeyError(f"No Table named {table_name}")
    
    def __iter__(self):
        return iter(self._name_list)

    def _get_by_id(self, table_id):
        return self[self._name_lookup[table_id]]
    
    def clear_cache(self):
        for batch_table in self._batch_tables.values():
            batch_table.clear_cache() 


batch_tables = BatchTables()


def get_table_by_id(table_id):
    return batch_tables._get_by_id(table_id)
