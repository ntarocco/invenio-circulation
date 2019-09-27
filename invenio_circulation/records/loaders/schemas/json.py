# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CERN.
# Copyright (C) 2019 RERO.
#
# invenio-circulation is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Circulation record loaders JSON schemas."""

from datetime import date, datetime

import arrow
from flask_babelex import lazy_gettext as _
from invenio_records_rest.schemas import RecordMetadataSchemaJSONV1
from invenio_records_rest.schemas.fields import PersistentIdentifier
from marshmallow import ValidationError, fields


class DateTimeString(fields.DateTime):
    """Custom DateTime field to return a string representation."""

    def __init__(self, **kwargs):
        """Constructor."""
        kwargs.setdefault('validate', self.validate_timezone)
        super().__init__(**kwargs)

    def validate_timezone(self, value):
        """Validate that the passed timezone, if any, is UTC."""
        # strong validation of input datetime to require UTC timezone
        if arrow.get(value).isoformat() != \
                arrow.get(value).to('utc').isoformat():
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
    item_pid = fields.Str()
    patron_pid = fields.Str(required=True)
    pid = PersistentIdentifier()
    pickup_location_pid = fields.Str()
    request_expire_date = DateString()
    request_start_date = DateString()
    start_date = DateString()
    transaction_date = DateTimeString()
    transaction_location_pid = fields.Str(required=True)
    transaction_user_pid = fields.Str(required=True)
