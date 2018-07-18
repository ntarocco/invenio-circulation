# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 CERN.
# Copyright (C) 2018 RERO.
#
# Invenio-Circulation is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Circulation minters."""

from invenio_circulation.config import _CIRCULATION_LOAN_PID_TYPE
from invenio_circulation.pid.providers import CirculationLoanIdProvider


def loanid_minter(record_uuid, data):
    """Mint loan identifiers."""
    assert _CIRCULATION_LOAN_PID_TYPE not in data
    provider = CirculationLoanIdProvider.create(
        object_type='rec',
        object_uuid=record_uuid,
    )
    data[_CIRCULATION_LOAN_PID_TYPE] = provider.pid.pid_value
    return provider.pid
