# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 CERN.
# Copyright (C) 2018 RERO.
#
# Invenio-Circulation is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Circulation PID providers."""

from invenio_pidstore.models import PIDStatus
from invenio_pidstore.providers.recordid import RecordIdProvider

from invenio_circulation.config import _CIRCULATION_LOAN_PID_TYPE


class CirculationLoanIdProvider(RecordIdProvider):
    """Record identifier provider."""

    pid_type = _CIRCULATION_LOAN_PID_TYPE
    """Type of persistent identifier."""

    pid_provider = None
    """Provider name.

    The provider name is not recorded in the PID since the provider does not
    provide any additional features besides creation of record ids.
    """

    default_status = PIDStatus.REGISTERED
    """Record IDs are by default registered immediately."""
