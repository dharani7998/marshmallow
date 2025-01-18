"""Decorators for registering schema pre-processing and post-processing methods.
These should be imported from the top-level `marshmallow` module.

Methods decorated with
`pre_load <marshmallow.decorators.pre_load>`, `post_load <marshmallow.decorators.post_load>`,
`pre_dump <marshmallow.decorators.pre_dump>`, `post_dump <marshmallow.decorators.post_dump>`,
and `validates_schema <marshmallow.decorators.validates_schema>` receive
``many`` as a keyword argument. In addition, `pre_load <marshmallow.decorators.pre_load>`,
`post_load <marshmallow.decorators.post_load>`,
and `validates_schema <marshmallow.decorators.validates_schema>` receive
``partial``. If you don't need these arguments, add ``**kwargs`` to your method
signature.


Example: ::

    from marshmallow import (
        Schema,
        pre_load,
        pre_dump,
        post_load,
        validates_schema,
        validates,
        fields,
        ValidationError,
    )


    class UserSchema(Schema):
        email = fields.Str(required=True)
        age = fields.Integer(required=True)

        @post_load
        def lowerstrip_email(self, item, many, **kwargs):
            item["email"] = item["email"].lower().strip()
            return item

        @pre_load(pass_collection=True)
        def remove_envelope(self, data, many, **kwargs):
            namespace = "results" if many else "result"
            return data[namespace]

        @post_dump(pass_collection=True)
        def add_envelope(self, data, many, **kwargs):
            namespace = "results" if many else "result"
            return {namespace: data}

        @validates_schema
        def validate_email(self, data, **kwargs):
            if len(data["email"]) < 3:
                raise ValidationError("Email must be more than 3 characters", "email")

        @validates("age")
        def validate_age(self, data, **kwargs):
            if data < 14:
                raise ValidationError("Too young!")

.. note::
    These decorators only work with instance methods. Class and static
    methods are not supported.

.. warning::
    The invocation order of decorated methods of the same type is not guaranteed.
    If you need to guarantee order of different processing steps, you should put
    them in the same processing method.
"""

from __future__ import annotations

import functools
from collections import defaultdict
from typing import Any, Callable, cast

PRE_DUMP = "pre_dump"
POST_DUMP = "post_dump"
PRE_LOAD = "pre_load"
POST_LOAD = "post_load"
VALIDATES = "validates"
VALIDATES_SCHEMA = "validates_schema"


class MarshmallowHook:
    __marshmallow_hook__: dict[str, list[tuple[bool, Any]]] | None = None


def validates(field_name: str) -> Callable[..., Any]:
    """Register a field validator.

    :param field_name: Name of the field that the method validates.
    """
    return set_hook(None, VALIDATES, field_name=field_name)


def validates_schema(
    fn: Callable[..., Any] | None = None,
    pass_collection: bool = False,  # noqa: FBT001, FBT002
    pass_original: bool = False,  # noqa: FBT001, FBT002
    skip_on_field_errors: bool = True,  # noqa: FBT001, FBT002
) -> Callable[..., Any]:
    """Register a schema-level validator.

    By default it receives a single object at a time, transparently handling the ``many``
    argument passed to the `Schema <marshmallow.Schema>`'s :func:`~marshmallow.Schema.validate` call.
    If ``pass_collection=True``, the raw data (which may be a collection) is passed.

    If ``pass_original=True``, the original data (before unmarshalling) will be passed as
    an additional argument to the method.

    If ``skip_on_field_errors=True``, this validation method will be skipped whenever
    validation errors have been detected when validating fields.

    .. versionchanged:: 3.0.0b1
        ``skip_on_field_errors`` defaults to `True`.
    .. versionchanged:: 3.0.0
        ``partial`` and ``many`` are always passed as keyword arguments to
        the decorated method.
    .. versionchanged:: 4.0.0
        ``unknown`` is passed as a keyword argument to the decorated method.
    """
    return set_hook(
        fn,
        VALIDATES_SCHEMA,
        many=pass_collection,
        pass_original=pass_original,
        skip_on_field_errors=skip_on_field_errors,
    )


def pre_dump(
    fn: Callable[..., Any] | None = None,
    pass_collection: bool = False,  # noqa: FBT001, FBT002
) -> Callable[..., Any]:
    """Register a method to invoke before serializing an object. The method
    receives the object to be serialized and returns the processed object.

    By default it receives a single object at a time, transparently handling the ``many``
    argument passed to the `Schema <marshmallow.Schema>`'s :func:`~marshmallow.Schema.dump` call.
    If ``pass_collection=True``, the raw data (which may be a collection) is passed.

    .. versionchanged:: 3.0.0
        ``many`` is always passed as a keyword arguments to the decorated method.
    """
    return set_hook(fn, PRE_DUMP, many=pass_collection)


def post_dump(
    fn: Callable[..., Any] | None = None,
    pass_collection: bool = False,  # noqa: FBT001, FBT002
    pass_original: bool = False,  # noqa: FBT001, FBT002
) -> Callable[..., Any]:
    """Register a method to invoke after serializing an object. The method
    receives the serialized object and returns the processed object.

    By default it receives a single object at a time, transparently handling the ``many``
    argument passed to the `Schema <marshmallow.Schema>`'s :func:`~marshmallow.Schema.dump` call.
    If ``pass_collection=True``, the raw data (which may be a collection) is passed.

    If ``pass_original=True``, the original data (before serializing) will be passed as
    an additional argument to the method.

    .. versionchanged:: 3.0.0
        ``many`` is always passed as a keyword arguments to the decorated method.
    """
    return set_hook(fn, POST_DUMP, many=pass_collection, pass_original=pass_original)


def pre_load(
    fn: Callable[..., Any] | None = None,
    pass_collection: bool = False,  # noqa: FBT001, FBT002
) -> Callable[..., Any]:
    """Register a method to invoke before deserializing an object. The method
    receives the data to be deserialized and returns the processed data.

    By default it receives a single object at a time, transparently handling the ``many``
    argument passed to the `Schema <marshmallow.Schema>`'s :func:`~marshmallow.Schema.load` call.
    If ``pass_collection=True``, the raw data (which may be a collection) is passed.

    .. versionchanged:: 3.0.0
        ``partial`` and ``many`` are always passed as keyword arguments to
        the decorated method.
    .. versionchanged:: 4.0.0
        ``unknown`` is passed as a keyword argument to the decorated method.
    """
    return set_hook(fn, PRE_LOAD, many=pass_collection)


def post_load(
    fn: Callable[..., Any] | None = None,
    pass_collection: bool = False,  # noqa: FBT001, FBT002
    pass_original: bool = False,  # noqa: FBT001, FBT002
) -> Callable[..., Any]:
    """Register a method to invoke after deserializing an object. The method
    receives the deserialized data and returns the processed data.

    By default it receives a single object at a time, transparently handling the ``many``
    argument passed to the `Schema <marshmallow.Schema>`'s :func:`~marshmallow.Schema.load` call.
    If ``pass_collection=True``, the raw data (which may be a collection) is passed.

    If ``pass_original=True``, the original data (before deserializing) will be passed as
    an additional argument to the method.

    .. versionchanged:: 3.0.0
        ``partial`` and ``many`` are always passed as keyword arguments to
        the decorated method.
    .. versionchanged:: 4.0.0
        ``unknown`` is passed as a keyword argument to the decorated method.
    """
    return set_hook(fn, POST_LOAD, many=pass_collection, pass_original=pass_original)


def set_hook(
    fn: Callable[..., Any] | None,
    tag: str,
    many: bool = False,  # noqa: FBT001, FBT002
    **kwargs: Any,
) -> Callable[..., Any]:
    """Mark decorated function as a hook to be picked up later.
    You should not need to use this method directly.

    .. note::
        Currently only works with functions and instance methods. Class and
        static methods are not supported.

    :return: Decorated function if supplied, else this decorator with its args
        bound.
    """
    # Allow using this as either a decorator or a decorator factory.
    if fn is None:
        return functools.partial(set_hook, tag=tag, many=many, **kwargs)

    # Set a __marshmallow_hook__ attribute instead of wrapping in some class,
    # because I still want this to end up as a normal (unbound) method.
    function = cast(MarshmallowHook, fn)
    try:
        hook_config = function.__marshmallow_hook__
    except AttributeError:
        function.__marshmallow_hook__ = hook_config = defaultdict(list)
    # Also save the kwargs for the tagged function on
    # __marshmallow_hook__, keyed by <tag>
    if hook_config is not None:
        hook_config[tag].append((many, kwargs))

    return fn
