# -*- coding: utf-8 -*-
#
# Copyright (C) 2018-2020 CERN.
# Copyright (C) 2018-2020 RERO.
#
# Invenio-Circulation is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Circulation exceptions."""

import json

from flask import g
from invenio_rest.errors import RESTException


class CirculationException(RESTException):
    """Base Exception for circulation module, inherit, don't raise."""

    code = 400

    @property
    def name(self):
        """The status name."""
        return type(self).__name__

    def get_body(self, environ=None):
        """Get the request body."""
        body = dict(
            status=self.code,
            message=self.get_description(environ),
            error_module="Circulation",
            error_class=self.name,
        )

        errors = self.get_errors()
        if self.errors:
            body["errors"] = errors

        if self.code and (self.code >= 500) and hasattr(g, "sentry_event_id"):
            body["error_id"] = str(g.sentry_event_id)

        return json.dumps(body)


# Permissions
class InvalidPermissionError(CirculationException):
    """Raised when permissions are not satisfied for transition."""

    code = 403

    def __init__(self, permission=None, **kwargs):
        """Initialize exception."""
        self.description = (
            "This action is not permitted "
            "for your role '{}'".format(permission)
        )
        super().__init__(**kwargs)


# Transitions
class TransitionConstraintsViolationError(CirculationException):
    """Exception raised when constraints for the transition failed."""

    _default = "Transition constraints have failed."


class TransitionConditionsFailedError(CirculationException):
    """Conditions for the transition failed at loan state."""

    description = "Transition conditions have failed."


class NoValidTransitionAvailableError(CirculationException):
    """Exception raised when all transitions conditions failed."""

    def __init__(self, loan_pid=None, state=None, **kwargs):
        """Initialize exception."""
        self.description = (
            "For the loan #'{0}' there are no valid transitions from "
            "its current state '{1}'".format(loan_pid, state)
        )
        super().__init__(**kwargs)


# Loans
class InvalidLoanStateError(CirculationException):
    """State not found in circulation configuration."""

    def __init__(self, state=None, **kwargs):
        """Initialize exception."""
        self.description = "Invalid loan state '{}'".format(state)
        super().__init__(**kwargs)


class ItemNotAvailableError(CirculationException):
    """Exception raised from action on unavailable item."""

    def __init__(self, item_pid=None, transition=None, **kwargs):
        """Initialize exception.

        :param item_pid: a dict containing `value` and `type` fields to
            uniquely identify the item.
        :param transition: the transition that failed.
        """
        self.description = "The item requested with PID '{0}:{1}' is not " \
                           "available. Transition to '{2}' has failed." \
            .format(item_pid["type"], item_pid["value"], transition)
        super().__init__(**kwargs)


class DocumentNotAvailableError(CirculationException):
    """Exception raised from action on unavailable document."""

    def __init__(self, document_pid=None, transition=None, **kwargs):
        """Initialize exception."""
        self.description = (
            "The document requested with PID '{0}' is not available. "
            "Transition to '{1}' has failed.".format(document_pid, transition)
        )
        super().__init__(**kwargs)


class ItemDoNotMatchError(CirculationException):
    """Exception raised from action on unavailable item."""


class DocumentDoNotMatchError(CirculationException):
    """Exception raised from action on unavailable document."""


class MultipleLoansOnItemError(CirculationException):
    """Exception raised when more than one loan on an item."""

    def __init__(self, item_pid=None, **kwargs):
        """Initialize exception.

        :param item_pid: a dict containing `value` and `type` fields to
            uniquely identify the item.
        """
        self.description = "Multiple active loans on item with PID '{0}:{1}'" \
            .format(item_pid["type"], item_pid["value"])
        super().__init__(**kwargs)


class LoanMaxExtensionError(CirculationException):
    """Exception raised when reached the max extensions for a loan."""

    def __init__(self, loan_pid=None, extension_count=None, **kwargs):
        """Initialize exception."""
        self.description = (
            "You have reached the maximum amount of extensions '{}' "
            "for loan '{}'".format(extension_count, loan_pid)
        )
        super().__init__(**kwargs)


# General
class RecordCannotBeRequestedError(CirculationException):
    """Exception raised when item can not be requested."""


class NotImplementedConfigurationError(CirculationException):
    """Exception raised when function is not implemented."""

    description = (
        "Function is not implemented. Implement this function in your module "
        "and pass it to the config variable"
    )

    def __init__(self, config_variable=None, **kwargs):
        """Initialize exception."""
        self.description = "{} '{}'".format(self.description, config_variable)
        super().__init__(**kwargs)


class MissingRequiredParameterError(CirculationException):
    """Exception raised when required parameter is missing."""
