from .auto_batch import unwrap_any_input_rows, wrap_row
import anvil.users


def force_login(*args, **kwargs):
    return unwrap_any_input_rows(anvil.users.force_login)(*args, **kwargs)


def get_user(*args, **kwargs):
    return wrap_row(anvil.users.get_user(*args, **kwargs))
