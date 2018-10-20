# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 CERN.
#
# invenio-app-ils is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Circulation permissions."""

from __future__ import absolute_import, print_function

from functools import wraps

from flask import abort, current_app
from flask_login import current_user
from invenio_access import action_factory
from invenio_access.permissions import Permission
from invenio_records_rest.utils import allow_all

loan_access = action_factory('loan-read-access')


def check_permission(permission):
    """Abort if permission is not allowed.

    :param permission: The permission to check.
    """
    if permission is not None and not permission.can():
        if current_user.is_authenticated:
            abort(403, 'You do not have a permission for this action')
        abort(401)


def has_read_loan_permission(*args, **kwargs):
    """Return permission to allow user to access loan."""
    return Permission(loan_access)


def loan_reader(*args, **kwargs):
    """Return an object which by default allows to read the load object."""
    def can(self):
        """Return True if user can read the loan record."""
        return has_read_loan_permission(*args, **kwargs).can()

    return type('Allow', (), {'can': can})()


def login_required(*args, **kwargs):
    """Return an object that evaluates if the current user is authenticated."""
    def can(self):
        """Return True if user is authenticated."""
        return current_user.is_authenticated

    return type('LoginRequired', (), {'can': can})()


def views_permissions_factory(action):
    """Default circulation views permissions factory."""
    if action == 'loan-read-access':
        return allow_all()
    elif action == 'loan-actions':
        return allow_all()


def need_permissions(action):
    """View decorator to check permissions for the given action or abort.

    :param action: The action needed.
    """
    def decorator_builder(f):
        @wraps(f)
        def decorate(*args, **kwargs):
            check_permission(
                current_app
                .config['CIRCULATION_VIEWS_PERMISSIONS_FACTORY'](action)
            )
            return f(*args, **kwargs)
        return decorate
    return decorator_builder
