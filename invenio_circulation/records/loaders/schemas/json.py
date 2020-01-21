# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2020 CERN.
# Copyright (C) 2019-2020 RERO.
#
# invenio-circulation is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Circulation record loaders JSON schemas."""

from datetime import date, datetime

import arrow
from flask import current_app
from flask_babelex import lazy_gettext as _
from invenio_records_rest.schemas import RecordMetadataSchemaJSONV1
from invenio_records_rest.schemas.fields import PersistentIdentifier
from marshmallow import Schema, ValidationError, fields, validates


class DateTimeString(fields.DateTime):
    """Custom DateTime field to return a string representation."""

    def __init__(self, **kwargs):
        """Constructor."""
        kwargs.setdefault("validate", self.validate_timezone)
        super().__init__(**kwargs)

    def validate_timezone(self, value):
        """Validate that the passed timezone, if any, is UTC."""
        # strong validation of input datetime to require UTC timezone
        if (
            arrow.get(value).isoformat() !=
            arrow.get(value).to("utc").isoformat()
        ):
            raise ValidationError(_("Not a valid ISO-8601 UTC datetime."))

    def deserialize(self, value, attr=None, data=None, **kwargs):
        """Validate ISO8601 datetime input but return the string value."""
        # value and _value can be <marshmallow.missing>
        _value = super().deserialize(value, attr, data, **kwargs)
        # return the value as string after marshmallow validation
        # because Invenio does not support Python datetime JSON serializer yet
        if _value and type(_value) == datetime:
            return _value.isoformat()
        return _value


class DateString(fields.Date):
    """Custom Date field to return a string representation."""

    def deserialize(self, value, attr=None, data=None, **kwargs):
        """Validate ISO8601 date input but return the string value."""
        # value and _value can be <marshmallow.missing>
        _value = super().deserialize(value, attr, data, **kwargs)
        # return the value as string after marshmallow validation
        # because Invenio does not support Python datetime JSON serializer yet
        if _value and type(_value) == date:
            return _value.isoformat()
        return _value


class LoanItemPIDSchemaV1(Schema):
    """Loan item PID Schema."""

    type = fields.Str(required=True)
    value = fields.Str(required=True)


class LoanSchemaV1(RecordMetadataSchemaJSONV1):
    """Loan schema."""

    class Meta:
        """Meta attributes for the schema."""

        from marshmallow import EXCLUDE

        unknown = EXCLUDE

    def get_pid_field(self):
        """Return loan PID field name."""
        return "pid"

    cancel_reason = fields.Str()
    document_pid = fields.Str()
    end_date = DateString()
    extension_count = fields.Integer()
    item_pid = fields.Nested(LoanItemPIDSchemaV1)
    patron_pid = fields.Str(required=True)
    pid = PersistentIdentifier()
    pickup_location_pid = fields.Str()
    request_expire_date = DateString()
    request_start_date = DateString()
    start_date = DateString()
    transaction_date = DateTimeString()
    transaction_location_pid = fields.Str(required=True)
    transaction_user_pid = fields.Str(required=True)

    @validates("transaction_location_pid")
    def validate_transaction_location_pid(self, value,  **kwargs):
        """Validate transaction_location_pid field."""
        transaction_location_is_valid = current_app.config[
            "CIRCULATION_TRANSACTION_LOCATION_VALIDATOR"
        ]
        if not transaction_location_is_valid(value):
            raise ValidationError(
                _("The loan `transaction_location_pid` is not valid."),
                field_names=["transaction_location_pid"],
            )

    @validates("transaction_user_pid")
    def validate_transaction_user_pid(self, value, **kwargs):
        """Validate transaction_user_pid field."""
        transaction_user_is_valid = current_app.config[
            "CIRCULATION_TRANSACTION_USER_VALIDATOR"
        ]
        if not transaction_user_is_valid(value):
            raise ValidationError(
                _("The loan `transaction_user_pid` is not valid."),
                field_names=["transaction_user_pid"],
            )


class LoanReplaceItemSchemaV1(RecordMetadataSchemaJSONV1):
    """Loan replace item schema."""

    class Meta:
        """Meta attributes for the schema."""

        from marshmallow import EXCLUDE

        unknown = EXCLUDE

    item_pid = fields.Nested(LoanItemPIDSchemaV1, required=True)
