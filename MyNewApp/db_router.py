"""
FieldOfficeRouter
─────────────────
Routes Child, Attendance, and Flag reads/writes to the database that
belongs to the currently-active field office.

The active database alias is stored in a thread-local variable
(`_db_alias`) so each request can set it independently.

Usage in views:
    from MyNewApp.db_router import set_db_alias
    set_db_alias(request.user.profile.db_alias)
"""

import threading

_thread_local = threading.local()

# Models that live in a field-office database
_FO_MODELS = {'child', 'attendance', 'flag'}

# Models that always live in the default DB (auth, sessions, profiles…)
_DEFAULT_MODELS = {'user', 'userprofile', 'permission', 'group',
                   'contenttype', 'session', 'logentry',
                   'mymodel', 'testmodel', 'aboutme'}


def set_db_alias(alias: str):
    """Call this at the top of any view that touches field-office data."""
    _thread_local.db_alias = alias


def get_db_alias() -> str:
    return getattr(_thread_local, 'db_alias', 'default')


class FieldOfficeRouter:
    """
    • Child / Attendance / Flag  →  current field-office DB
    • Everything else            →  default DB
    """

    def _is_fo_model(self, model) -> bool:
        return model.__name__.lower() in _FO_MODELS

    def db_for_read(self, model, **hints):
        if self._is_fo_model(model):
            return get_db_alias()
        return 'default'

    def db_for_write(self, model, **hints):
        if self._is_fo_model(model):
            return get_db_alias()
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        # Allow relations within the same database group
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if model_name and model_name.lower() in _FO_MODELS:
            # Migrate FO tables to every FO database, not to default
            return db != 'default'
        # Migrate all other tables only to the default DB
        return db == 'default'
