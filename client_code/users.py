from .auto_batch import USE_WRAPPED
from . import _users
import anvil.users


def __getattr__(attr):
    if USE_WRAPPED and attr in ('force_login', 'get_user'):
        return getattr(_users, attr)
    else:
        return getattr(anvil.users, attr)
