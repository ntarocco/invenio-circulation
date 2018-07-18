# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 CERN.
# Copyright (C) 2018 RERO.
#
# Invenio-Circulation is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module for the circulation of bibliographic items."""

from .utils import is_checkout_valid, item_location_retriever

CIRCULATION_ITEM_LOCATION_RETRIEVER = item_location_retriever
"""."""

CIRCULATION_POLICIES = dict(checkout=is_checkout_valid)
"""."""

_CIRCULATION_LOAN_PID_TYPE = 'loanid'
"""."""

_CIRCULATION_LOAN_MINTER = 'circ_loanid'
"""."""

_CIRCULATION_LOAN_FETCHER = 'circ_loanid'
"""."""

CIRCULATION_REST_ENDPOINTS = dict(
    loanid=dict(
        pid_type=_CIRCULATION_LOAN_PID_TYPE,
        pid_minter=_CIRCULATION_LOAN_MINTER,
        pid_fetcher=_CIRCULATION_LOAN_FETCHER,
        # search_class=RecordsSearch,
        # indexer_class=RecordIndexer,
        search_index=None,
        search_type=None,
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
