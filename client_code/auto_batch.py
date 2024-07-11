import anvil.tables
from anvil.server import portable_class
from collections import defaultdict
from functools import wraps


_add_queue = defaultdict(dict)
_update_queue = defaultdict(dict)
_delete_queue = []
_batching = False


def process_batch_add():
    global _add_queue
    for batch_table in _add_queue:
        batch_rows = list(_add_queue[batch_table].keys())
        column_values_list = [column_values for column_values in _add_queue[batch_table].values()]
        rows = batch_table.table.add_rows(column_values_list)
        for i, row in enumerate(rows):
            batch_rows[i].row = row
            BatchTable.of_row(row).add_batch_row(batch_rows[i])
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


@portable_class
class BatchRow(anvil.tables.Row):
    def __init__(self, row):
        self._row = row
        self._cache = {} # debatchified
        self._deleted = False

    @staticmethod
    def from_batched_add(column_values):
        batch_row = BatchRow(None)
        batch_row._cache = column_values
        return batch_row
    
    @property
    def row(self):
        if not self._row:
            if _add_queue:
                print("AutoBatch: process_batch_add triggered early by BatchRow.row")
            process_batch_add()
        return self._row

    @row.setter
    def row(self, value):
        self._row = value

    # @property
    # @if_not_deleted
    # def _id(self):
    #     return self.row._id

    # @property
    # @if_not_deleted
    # def _table_id(self):
    #     return self.row._table_id

    # @if_not_deleted
    # def __eq__(self, other):
    #     if not isinstance(other, BaseRow):
    #         return NotImplemented
    #     return other._id == self._id and other._table_id == self._table_id

    # @if_not_deleted
    # def __hash__(self):
    #     return id(self)
    
    @if_not_deleted
    def __repr__(self):
        if self._row:
            return f"BatchRow({repr(self._row)})"
        else:
            return f"BatchRow.from_batched_add({repr(self._cache)})"
    
    @if_not_deleted
    def __iter__(self):
        return iter(dict(self._row).items())
    
    @if_not_deleted
    def __getitem__(self, column):
        if column in self._cache:
            return _batchify(self._cache[column])
        value = self.row[column]
        if _batching:
            self._cache[column] = value
        return _batchify(value)

    @if_not_deleted
    def __setitem__(self, column, value):
        self.update(**{column: value})

    @if_not_deleted
    def update(self, **column_values):
        global _update_queue
        debatchified_column_values = _debatchify_column_values(column_values)
        if not _batching:
            return self.row.update(**debatchified_column_values)
        _update_queue[self].update(debatchified_column_values)
        self._cache.update(debatchified_column_values)

    @if_not_deleted
    def delete(self):
        global _delete_queue
        self._deleted = True
        if not _batching:
            return self.row.delete()
        _delete_queue.append(self)
            
    @if_not_deleted
    def get_id(self):
        return self.row.get_id()

    def clear_cache(self):
        self._cache.clear()


def _debatchify_column_values(column_values):
    return {column: debatchify(value) for column, value in column_values.items()}


def _batchify(value):
    def _is_row_but_not_batch_row(thing):
        return isinstance(thing, anvil.tables.Row) and not isinstance(thing, BatchRow)
        
    def _batchify_rows(rows):
        batch_table = BatchTable.of_row(rows[0])
        return [batch_table.get_batch_row(row) for row in rows]
        
    if _is_row_but_not_batch_row(value):
        return _batchify_rows([value])[0]
    elif isinstance(value, list) and value and _is_row_but_not_batch_row(value[0]):
        return _batchify_rows(value)
    else:
        return value


def debatchify(value):
    if isinstance(value, BatchRow):
        return value.row
    elif isinstance(value, list) and value and isinstance(value[0], BatchRow):
        return [batch_row.row for batch_row in value]
    else:
        return value


@portable_class
class BatchSearchIterator(anvil.tables.SearchIterator):
    def __init__(self, batch_table, search_iterator):
        self._batch_table = batch_table
        self._search_iterator = search_iterator
  
    def __len__(self):
        return len(self._search_iterator)

    def __getitem__(self, index):
        row = self._search_iterator[index]
        return self._batch_table.get_batch_row(row)


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
        return BatchSearchIterator(self, self.table.search(
            *[debatchify(arg) for arg in args], 
            **_debatchify_column_values(kwargs)
        ))

    def get(self, *args, **kwargs):
        if _add_queue or _update_queue or _delete_queue:
            print("AutoBatch: process_batch triggered early by get")
        process_batch()
        return self.get_batch_row(self.table.get(
            *[debatchify(arg) for arg in args], 
            **_debatchify_column_values(kwargs)
        ))
    
    def get_by_id(self, row_id, *args, **kwargs):
        if row_id in self._batch_rows:
            batch_row = self._batch_rows[row_id]
        else:
            row = self.table.get_by_id(row_id, *args, **kwargs)
            batch_row = self._get_new_batch_row(row)
        return batch_row

    def add_row(self, **column_values):
        global _add_queue
        debatchified_column_values = _debatchify_column_values(column_values)
        if not _batching:
            return _batchify(self.table.add_row(**debatchified_column_values))
        batch_row = BatchRow.from_batched_add(debatchified_column_values)
        _add_queue[self][batch_row] = debatchified_column_values
        return batch_row

    def add_rows(self, column_values_list):
        return [self.add_row(**column_values) for column_values in column_values_list]

    def delete_all_rows(self, *args, **kwargs):
        return self.table.delete_all_rows(*args, **kwargs) # TODO: try batching with other deletes

    def add_batch_row(self, batch_row):
        self._batch_rows[batch_row.row.get_id()] = batch_row
    
    def get_batch_row(self, row):
        if row is None:
            return None
        elif row.get_id() in self._batch_rows:
            return self._batch_rows[row.get_id()]
        else:
            return self._get_new_batch_row(row)
    
    def _get_new_batch_row(self, row):
        batch_row = BatchRow(row)
        if _batching:
            self._batch_rows[row.get_id()] = batch_row
        return batch_row

    def clear_cache(self):
        for batch_row in self._batch_rows.values():
            batch_row.clear_cache()
        self._batch_rows.clear()

    @staticmethod
    def of_row(row):
        return batch_tables.get_by_id(row._table_id)


@portable_class
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

    def get_by_id(self, table_id):
        return self[self._name_lookup[table_id]]
    
    def clear_cache(self):
        for batch_table in self._batch_tables.values():
            batch_table.clear_cache()


batch_tables = BatchTables()
