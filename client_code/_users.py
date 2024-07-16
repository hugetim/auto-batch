from .auto_batch import unwrap_any_input_rows, BatchRow
import anvil.users


def force_login(*args, **kwargs):
    return unwrap_any_input_rows(anvil.users.force_login)(*args, **kwargs)


def get_user(*args, **kwargs):
    raw_out = anvil.users.get_user(*args, **kwargs)
    return BatchRow(raw_out) if raw_out else None
