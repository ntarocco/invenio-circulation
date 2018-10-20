# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 CERN.
# Copyright (C) 2018 RERO.
#
# Invenio-Circulation is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Tests for loan search class."""

from invenio_circulation.api import Loan
from invenio_circulation.search import LoansSearch


def test_search_loans_by_pid(indexed_loans):
    """Test retrieve loan list belonging to an item."""
    loans = list(LoansSearch.search_loans_by_pid(item_pid="item_pending_1"))
    assert loans
    assert len(loans) == 1
    loan = Loan.get_record_by_pid(loans[0][Loan.pid_field])
    assert loan.get("item_pid") == "item_pending_1"

    loans = list(
        LoansSearch.search_loans_by_pid(
            item_pid="item_multiple_pending_on_loan_7",
            exclude_states=["ITEM_ON_LOAN"],
        )
    )
    assert len(loans) == 2


def test_search_loans_by_patron_pid(indexed_loans):
    """Test retrieve loan list belonging to a patron."""
    loans = list(LoansSearch.search_loans_by_patron_pid("1"))
    assert loans
    assert len(loans) == 8

    loans = list(LoansSearch.search_loans_by_patron_pid("2"))
    assert loans
    assert len(loans) == 3

    loans = list(LoansSearch.search_loans_by_patron_pid("3"))
    assert loans
    assert len(loans) == 1
