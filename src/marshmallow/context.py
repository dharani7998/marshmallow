"""Objects related to serializtion/deserialization context"""

import contextlib
import contextvars

CONTEXT = contextvars.ContextVar("context", default=None)


class Context(contextlib.AbstractContextManager):
    def __init__(self, context):
        self.context = context

    def __enter__(self):
        self.token = CONTEXT.set(self.context)

    def __exit__(self, *args, **kwargs):
        CONTEXT.reset(self.token)
