from .auto_batch import unwrap_any_input_rows, BatchTable
import anvil.users


def force_login(*args, **kwargs):
    return unwrap_any_input_rows(anvil.users.force_login)(*args, **kwargs)


def get_user(*args, **kwargs):
    user_row = anvil.users.get_user(*args, **kwargs)
    batch_table = BatchTable.of_row(user_row)
    return batch_table.get_batch_row(user_row)
