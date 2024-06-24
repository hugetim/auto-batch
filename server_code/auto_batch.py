import anvil.tables
from collections import defaultdict


_update_queue = defaultdict(dict)  # Queue for update operations
_batching = False


def process_batch():
    global _update_queue
    with anvil.tables.batch_update:
        for row, fields in _update_queue.items():
            row.update(**fields)
    _update_queue.clear()


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


class BatchRow(anvil.tables.Row):
    def __init__(self, row):
        self.row = row
        self._cache = {}
        
    def __getitem__(self, column):
        if column in self._cache:
            value = self._cache[column]
        else:
            value = batchify(self.row[column])
            if _batching:
                self._cache[column] = value
        return value
    
    def __setitem__(self, column, value):
        self.update(**{column: value})
    
    def update(self, **fields):
        debatchified_fields = BatchRow._debatchify_fields(fields)
        if _batching:
            if self.row not in _update_queue:
                _update_queue[self.row] = {}
            _update_queue[self.row].update(debatchified_fields)
            self._cache.update(debatchified_fields)
        else:
            self.row.update(**debatchified_fields)

    def delete(self):
        raise NotImplementedError
  
    def get_id(self):
        return self.row.get_id()

    def clear_cache(self):
        self._cache.clear()

    @staticmethod
    def _debatchify_fields(fields):
        return {key: debatchify(value) for key, value in fields.items()}


def batchify(value):
    def _batchify_rows(rows):
        batch_table = BatchTable.of_row(rows[0])
        return [batch_table.get_batch_row(row) for row in rows]
        
    if isinstance(value, anvil.tables.Row):
        return _batchify_rows([value])[0]
    elif isinstance(value, list) and value and isinstance(value[0], anvil.tables.Row):
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


class BatchSearchIterator(anvil.tables.SearchIterator):
    def __init__(self, batch_table, search_iterator):
        self._batch_table = batch_table
        self._search_iterator = search_iterator
  
    def __len__(self):
        return len(self._search_iterator)

    def __getitem__(self, index):
        row = self._search_iterator[index]
        return self._batch_table.get_batch_row(row)


class BatchTable(anvil.tables.Table):
    def __init__(self, table):
        self.table = table
        self._batch_rows = {}
        self.clear_cache()
        
    def search(self, *args, **kwargs):
        process_batch()
        return BatchSearchIterator(self, self.table.search(*args, **kwargs))

    def get(self, *args, **kwargs):
        process_batch()
        return self.get_batch_row(self.table.get(*args, **kwargs))
    
    def get_by_id(self, row_id):
        if row_id in self._batch_rows:
            batch_row = self._batch_rows[row_id]
        else:
            row = self.table.get_by_id(row_id)
            batch_row = self._get_new_batch_row(row)
        return batch_row

    def delete(self):
        raise NotImplementedError

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
