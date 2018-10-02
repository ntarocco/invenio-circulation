# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 CERN.
# Copyright (C) 2018 RERO.
#
# Invenio-Circulation is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module for the circulation of bibliographic items."""

from invenio_indexer.api import RecordIndexer
from invenio_records_rest.utils import allow_all

from .api import Loan
from .links import loan_links_factory
from .search import LoansSearch
from .transitions.transitions import CreatedToItemOnLoan, CreatedToPending, \
    ItemAtDeskToItemOnLoan, ItemInTransitHouseToItemReturned, \
    ItemOnLoanToItemInTransitHouse, ItemOnLoanToItemOnLoan, \
    ItemOnLoanToItemReturned, PendingToItemAtDesk, \
    PendingToItemInTransitPickup
from .utils import get_default_extension_duration, \
    get_default_extension_max_count, get_default_loan_duration, \
    is_item_available, is_loan_duration_valid, item_exists, \
    item_location_retriever, patron_exists

_CIRCULATION_LOAN_PID_TYPE = 'loanid'
"""Persistent Identifier for Loans."""

_CIRCULATION_LOAN_MINTER = 'loanid'
"""Minter PID for Loans."""

_CIRCULATION_LOAN_FETCHER = 'loanid'
"""Fetcher PID for Loans."""

_Loan_PID = 'pid(loanid,record_class="invenio_circulation.api:Loan")'
"""Loan PID url converter."""

CIRCULATION_ITEMS_RETRIEVER_FROM_DOCUMENT = None
"""Function that returns a list of item PIDs given a Document PID."""

CIRCULATION_DOCUMENT_RETRIEVER_FROM_ITEM = None
"""Function that returns the Document PID of a given Item PID."""

CIRCULATION_STATES_ITEM_AVAILABLE = ['ITEM_RETURNED', 'CANCELLED']
"""Defines the list of Loan states for which an Item is considered loanable.

Only Items that have these circulation statuses are available and loanable
by patrons."""

CIRCULATION_LOAN_TRANSITIONS_DEFAULT_PERMISSION_FACTORY = allow_all
"""Default permission factory for all Loans transitions."""

CIRCULATION_LOAN_TRANSITIONS = {
    'CREATED': [
        dict(dest='PENDING', trigger='request', transition=CreatedToPending),
        dict(dest='ITEM_ON_LOAN', trigger='checkout',
             transition=CreatedToItemOnLoan)
    ],
    'PENDING': [
        dict(dest='ITEM_AT_DESK', transition=PendingToItemAtDesk),
        dict(dest='ITEM_IN_TRANSIT_FOR_PICKUP',
             transition=PendingToItemInTransitPickup),
        dict(dest='CANCELLED', trigger='cancel')
    ],
    'ITEM_AT_DESK': [
        dict(dest='ITEM_ON_LOAN', transition=ItemAtDeskToItemOnLoan),
        dict(dest='CANCELLED', trigger='cancel')
    ],
    'ITEM_IN_TRANSIT_FOR_PICKUP': [
        dict(dest='ITEM_AT_DESK'),
        dict(dest='CANCELLED', trigger='cancel')
    ],
    'ITEM_ON_LOAN': [
        dict(dest='ITEM_RETURNED', transition=ItemOnLoanToItemReturned),
        dict(dest='ITEM_IN_TRANSIT_TO_HOUSE',
             transition=ItemOnLoanToItemInTransitHouse),
        dict(dest='ITEM_ON_LOAN', transition=ItemOnLoanToItemOnLoan,
             trigger='extend'),
        dict(dest='CANCELLED', trigger='cancel')
    ],
    'ITEM_IN_TRANSIT_TO_HOUSE': [
        dict(dest='ITEM_RETURNED',
             transition=ItemInTransitHouseToItemReturned),
        dict(dest='CANCELLED', trigger='cancel')
    ],
    'ITEM_RETURNED': [],
    'CANCELLED': [],
}
"""Default circulation Loans transitions."""

CIRCULATION_LOAN_INITIAL_STATE = 'CREATED'
"""Define the initial state name of a Loan."""

CIRCULATION_PATRON_EXISTS = patron_exists
"""Function that returns True if the given Patron exists."""

CIRCULATION_ITEM_EXISTS = item_exists
"""Function that returns True if the given Item exists."""

CIRCULATION_ITEM_LOCATION_RETRIEVER = item_location_retriever
"""Function that returns the Location PID of the given Item."""

CIRCULATION_POLICIES = dict(
    checkout=dict(
        duration_default=get_default_loan_duration,
        duration_validate=is_loan_duration_valid,
        item_available=is_item_available
    ),
    extension=dict(
        from_end_date=True,
        duration_default=get_default_extension_duration,
        max_count=get_default_extension_max_count
    ),
)
"""Default circulation policies when performing an action on a Loan."""

CIRCULATION_REST_ENDPOINTS = dict(
    loanid=dict(
        pid_type=_CIRCULATION_LOAN_PID_TYPE,
        pid_minter=_CIRCULATION_LOAN_MINTER,
        pid_fetcher=_CIRCULATION_LOAN_FETCHER,
        search_class=LoansSearch,
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
        item_route='/circulation/loan/<{0}:pid_value>'.format(_Loan_PID),
        default_media_type='application/json',
        links_factory_imp=loan_links_factory,
        max_result_window=10000,
        error_handlers=dict(),
        create_permission_factory_imp=allow_all
    ),
)
"""REST endpoint configuration for circulation APIs."""
