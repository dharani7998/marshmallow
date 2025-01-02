"""Objects related to serializtion/deserialization context"""

import contextlib
import contextvars

_CURRENT_CONTEXT: contextvars.ContextVar = contextvars.ContextVar("context")


class Context(contextlib.AbstractContextManager):
    def __init__(self, context):
        self.context = context

    def __enter__(self):
        self.token = _CURRENT_CONTEXT.set(self.context)

    def __exit__(self, *args, **kwargs):
        _CURRENT_CONTEXT.reset(self.token)

    @classmethod
    def get(cls, default=...):
        if default is not ...:
            return _CURRENT_CONTEXT.get(default)
        return _CURRENT_CONTEXT.get()
