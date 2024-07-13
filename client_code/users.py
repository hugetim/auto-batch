from ..auto_batch import debatchify_inputs, BatchTable
import anvil.users


def force_login(*args, **kwargs):
    return debatchify_inputs(anvil.users.force_login)(*args, **kwargs)


def get_user(*args, **kwargs):
    user_row = anvil.users.get_user(*args, **kwargs)
    batch_table = BatchTable.of_row(user_row)
    return batch_table.get_batch_row(user_row)


def __getattr__(attr):
    return getattr(anvil.users, attr)
