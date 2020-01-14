# -*- coding: utf-8 -*-
#
# Copyright (C) 2018-2020 CERN.
# Copyright (C) 2018-2020 RERO.
#
# Invenio-Circulation is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Tests for loan search class."""

from elasticsearch import VERSION as ES_VERSION

from invenio_circulation.api import Loan
from invenio_circulation.search.api import search_by_patron_item_or_document, \
    search_by_patron_pid, search_by_pid


def _assert_total(total, expected):
    """Assert total (ES6 compatibility)."""
    if ES_VERSION[0] >= 7:
        assert total.value == expected
    else:
        assert total == expected


def test_search_loans_by_pid(indexed_loans):
    """Test retrieve loan list belonging to an item."""
    item_pid = dict(type="itemid", value="item_pending_1")
    loans = list(
        search_by_pid(
            item_pid=item_pid
        ).scan()
    )
    assert len(loans) == 1
    loan = Loan.get_record_by_pid(loans[0]["pid"])
    assert loan["item_pid"] == item_pid


def test_search_loans_by_pid_filtering_states(indexed_loans):
    """Test retrieve loan list belonging to an item filtering states."""
    search = search_by_pid(
        item_pid=dict(type="itemid", value="item_multiple_pending_on_loan_7"),
        filter_states=["PENDING", "ITEM_ON_LOAN"],
    )
    search_result = search.execute()
    _assert_total(search_result.hits.total, 3)


def test_search_loans_by_pid_excluding_states(indexed_loans):
    """Test retrieve loan list belonging to an item excluding states."""
    search_result = search_by_pid(
        item_pid=dict(type="itemid", value="item_multiple_pending_on_loan_7"),
        exclude_states=["ITEM_ON_LOAN"],
    ).execute()
    _assert_total(search_result.hits.total, 2)


def test_search_loans_by_patron_pid(indexed_loans):
    """Test retrieve loan list belonging to a patron."""
    search_result = search_by_patron_pid("1").execute()
    _assert_total(search_result.hits.total, 8)

    search_result = search_by_patron_pid("2").execute()
    _assert_total(search_result.hits.total, 3)

    search_result = search_by_patron_pid("3").execute()
    _assert_total(search_result.hits.total, 1)


def test_search_loans_by_patron_and_item_or_document(indexed_loans):
    """Test retrieve loan list by patron and items."""
    search_result = search_by_patron_item_or_document(
        patron_pid="1", item_pid=dict(type="itemid", value="item_returned_3")
    ).execute()
    _assert_total(search_result.hits.total, 1)

    search_result = search_by_patron_item_or_document(
        patron_pid="1", item_pid=dict(type="itemid", value="not_existing")
    ).execute()
    _assert_total(search_result.hits.total, 0)

    search_result = search_by_patron_item_or_document(
        patron_pid="999999",
        item_pid=dict(type="itemid", value="item_returned_3"),
    ).execute()
    _assert_total(search_result.hits.total, 0)

    search_result = search_by_patron_item_or_document(
        patron_pid="1", document_pid="document_pid"
    ).execute()
    _assert_total(search_result.hits.total, 8)

    search_result = search_by_patron_item_or_document(
        patron_pid="1", document_pid="not_existing"
    ).execute()
    _assert_total(search_result.hits.total, 0)

    search_result = search_by_patron_item_or_document(
        patron_pid="999999", document_pid="document_returned_1"
    ).execute()
    _assert_total(search_result.hits.total, 0)


def test_search_loans_by_patron_and_item_or_document_filtering_states(
    indexed_loans
):
    """Test retrieve loan list by patron and items filtering states."""
    search = search_by_patron_item_or_document(
        patron_pid="1",
        item_pid=dict(type="itemid", value="item_returned_3"),
        filter_states=["ITEM_RETURNED"],
    )
    search_result = search.execute()
    _assert_total(search_result.hits.total, 1)

    search = search_by_patron_item_or_document(
        patron_pid="1",
        item_pid=dict(type="itemid", value="item_returned_3"),
        filter_states=["ITEM_AT_DESK"],
    )
    search_result = search.execute()
    _assert_total(search_result.hits.total, 0)

    search = search_by_patron_item_or_document(
        patron_pid="1",
        document_pid="document_pid",
        filter_states=["ITEM_RETURNED"],
    )
    search_result = search.execute()
    _assert_total(search_result.hits.total, 2)

    search = search_by_patron_item_or_document(
        patron_pid="2",
        document_pid="document_pid",
        filter_states=["ITEM_RETURNED"],
    )
    search_result = search.execute()
    _assert_total(search_result.hits.total, 1)

    search = search_by_patron_item_or_document(
        patron_pid="1",
        document_pid="document_pid",
        filter_states=["ITEM_AT_DESK"],
    )
    search_result = search.execute()
    _assert_total(search_result.hits.total, 1)

    search = search_by_patron_item_or_document(
        patron_pid="1", document_pid="document_pid", filter_states=["PENDING"]
    )
    search_result = search.execute()
    _assert_total(search_result.hits.total, 3)
