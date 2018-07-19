# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 CERN.
# Copyright (C) 2018 RERO.
#
# Invenio-Circulation is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module for the circulation of bibliographic items."""

from .api import Loan
from .utils import is_checkout_valid, item_location_retriever

CIRCULATION_ITEM_LOCATION_RETRIEVER = item_location_retriever
"""."""

CIRCULATION_POLICIES = dict(checkout=is_checkout_valid)
"""."""

CIRCULATION_LOAN_TRANSITIONS = [{
    'trigger': 'request',
    'source': 'CREATED',
    'dest': 'PENDING',
    'before': 'set_request_parameters'
}, {
    'trigger': 'validate_request',
    'source': 'PENDING',
    'dest': 'ITEM_IN_TRANSIT',
    'before': 'set_parameters',
    'unless': 'is_pickup_at_same_library'
}, {
    'trigger': 'validate_request',
    'source': 'PENDING',
    'dest': 'ITEM_AT_DESK',
    'before': 'set_parameters',
    'conditions': 'is_pickup_at_same_library'
}, {
    'trigger': 'checkout',
    'source': 'CREATED',
    'dest': 'ITEM_ON_LOAN',
    'before': 'set_parameters',
    'conditions': 'is_checkout_valid'
}, {
    'trigger': 'checkin',
    'source': 'ITEM_ON_LOAN',
    'dest': 'ITEM_RETURNED',
    'before': 'set_parameters'
}]
"""."""

CIRCULATION_LOAN_STATES = [
    'CREATED',
    'PENDING',
    'ITEM_ON_LOAN',
    'ITEM_RETURNED',
    'ITEM_IN_TRANSIT',
    'ITEM_AT_DESK',
]

CIRCULATION_LOAN_PID_TYPE = 'loanid'
"""."""

CIRCULATION_LOAN_MINTER = 'circ_loanid'
"""."""

CIRCULATION_LOAN_FETCHER = 'circ_loanid'
"""."""

CIRCULATION_LOAN_ITEM_ROUTE = '/circulation/loan/<pid(loanid):pid_value>'
"""."""



CIRCULATION_REST_ENDPOINTS = dict(
    loanid=dict(
        pid_type=CIRCULATION_LOAN_PID_TYPE,
        pid_minter=CIRCULATION_LOAN_MINTER,
        pid_fetcher=CIRCULATION_LOAN_FETCHER,
        # search_class=RecordsSearch,
        # indexer_class=RecordIndexer,
        search_index=None,
        search_type=None,
        record_class=Loan,
        record_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_response'),
        },
        search_serializers={
            'application/json': ('invenio_records_rest.serializers'
                                 ':json_v1_search'),
        },
        list_route='/circulation/loan/',
        item_route='/circulation/loan/<pid(loanid):pid_value>',
        default_media_type='application/json',
        max_result_window=10000,
        error_handlers=dict(),
    ),
)
"""."""
