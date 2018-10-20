# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 CERN.
# Copyright (C) 2018 RERO.
#
# Invenio-Circulation is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Tests for loan states."""

from datetime import timedelta

import mock
import pytest
from flask import current_app

from invenio_circulation.api import Loan, is_item_available
from invenio_circulation.errors import ItemNotAvailable, \
    NoValidTransitionAvailable, TransitionConstraintsViolation
from invenio_circulation.proxies import current_circulation
from invenio_circulation.utils import parse_date

from .helpers import SwappedConfig, SwappedNestedConfig


@mock.patch(
    "invenio_circulation.transitions.transitions"
    ".get_pending_loans_by_doc_pid"
)
def test_loan_checkout_checkin(
    mock_pending_loans_for_document,
    loan_created,
    db,
    params,
    mock_is_item_available,
):
    """Test loan checkout and checkin actions."""
    mock_pending_loans_for_document.return_value = []
    assert loan_created["state"] == "CREATED"

    loan = current_circulation.circulation.trigger(
        loan_created, **dict(params, trigger="checkout")
    )
    db.session.commit()
    assert loan["state"] == "ITEM_ON_LOAN"

    # set same transaction location to avoid "in transit"
    same_location = params["transaction_location_pid"]
    with SwappedConfig(
        "CIRCULATION_ITEM_LOCATION_RETRIEVER", lambda x: same_location
    ):
        loan = current_circulation.circulation.trigger(loan, **dict(params))
        db.session.commit()
        assert loan["state"] == "ITEM_RETURNED"


def test_loan_request(loan_created, db, params):
    """Test loan request action."""
    assert loan_created["state"] == "CREATED"

    loan = current_circulation.circulation.trigger(
        loan_created,
        **dict(
            params,
            trigger="request",
            pickup_location_pid="pickup_location_pid",
        )
    )
    db.session.commit()
    assert loan["state"] == "PENDING"


def test_loan_extend(loan_created, db, params, mock_is_item_available):
    """Test loan extend action."""

    def get_max_count_1(loan):
        return 1

    loan = current_circulation.circulation.trigger(
        loan_created, **dict(params, trigger="checkout")
    )
    db.session.commit()
    end_date = parse_date(loan["end_date"])

    loan = current_circulation.circulation.trigger(
        loan, **dict(params, trigger="extend")
    )
    db.session.commit()
    new_end_date = parse_date(loan["end_date"])
    assert new_end_date == end_date + timedelta(days=30)
    assert loan["extension_count"] == 1
    loan = current_circulation.circulation.trigger(
        loan, **dict(params, trigger="extend")
    )
    db.session.commit()

    # test to manny extensions
    current_app.config["CIRCULATION_POLICIES"]["extension"][
        "max_count"
    ] = get_max_count_1
    with pytest.raises(TransitionConstraintsViolation):
        loan = current_circulation.circulation.trigger(
            loan, **dict(params, trigger="extend")
        )


def test_loan_extend_from_enddate(
    loan_created, db, params, mock_is_item_available
):
    """Test loan extend action from transaction date."""

    loan = current_circulation.circulation.trigger(
        loan_created, **dict(params, trigger="checkout")
    )
    db.session.commit()
    extension_date = parse_date(loan.get("transaction_date"))
    current_app.config["CIRCULATION_POLICIES"]["extension"][
        "from_end_date"
    ] = False

    loan = current_circulation.circulation.trigger(
        loan, **dict(params, trigger="extend")
    )
    db.session.commit()
    new_end_date = parse_date(loan["end_date"])
    assert new_end_date == extension_date + timedelta(days=30)
    assert loan["extension_count"] == 1


def test_cancel_action(loan_created, db, params, mock_is_item_available):
    """Test should pass when calling `cancel` from `ITEM_ON_LOAN`."""
    loan = current_circulation.circulation.trigger(
        loan_created, **dict(params, trigger="checkout")
    )
    db.session.commit()

    current_circulation.circulation.trigger(
        loan_created, **dict(params, trigger="cancel")
    )
    assert loan["state"] == "CANCELLED"


def test_cancel_fail(loan_created, params):
    """Test should fail when calling `cancel` from `CREATED`."""
    with pytest.raises(NoValidTransitionAvailable):
        current_circulation.circulation.trigger(
            loan_created, **dict(params, trigger="cancel")
        )


def test_validate_item_in_transit_for_pickup(loan_created, db, params):
    """."""
    loan = current_circulation.circulation.trigger(
        loan_created,
        **dict(
            params,
            trigger="request",
            pickup_location_pid="pickup_location_pid",
        )
    )
    db.session.commit()
    assert loan["state"] == "PENDING"

    with SwappedConfig(
        "CIRCULATION_ITEM_LOCATION_RETRIEVER",
        lambda x: "external_location_pid",
    ):
        loan = current_circulation.circulation.trigger(loan, **dict(params))
        assert loan["state"] == "ITEM_IN_TRANSIT_FOR_PICKUP"


def test_validate_item_at_desk(loan_created, db, params):
    """."""
    loan = current_circulation.circulation.trigger(
        loan_created,
        **dict(
            params,
            trigger="request",
            pickup_location_pid="pickup_location_pid",
        )
    )
    db.session.commit()
    assert loan["state"] == "PENDING"

    with SwappedConfig(
        "CIRCULATION_ITEM_LOCATION_RETRIEVER", lambda x: "pickup_location_pid"
    ):
        loan = current_circulation.circulation.trigger(
            loan_created, **dict(params)
        )
        assert loan["state"] == "ITEM_AT_DESK"


def test_checkout_start_is_transaction_date(
    loan_created, db, params, mock_is_item_available
):
    """Test checkout start date to transaction date when not set."""
    number_of_days = 10

    with SwappedNestedConfig(
        ["CIRCULATION_POLICIES", "checkout", "duration_default"],
        lambda x: number_of_days,
    ):
        loan = current_circulation.circulation.trigger(
            loan_created, **dict(params, trigger="checkout")
        )
        db.session.commit()

        assert loan["state"] == "ITEM_ON_LOAN"
        assert loan["start_date"] == loan["transaction_date"]
        start_date = parse_date(loan["start_date"])
        end_date = start_date + timedelta(number_of_days)
        assert loan["end_date"] == end_date.isoformat()


def test_checkout_with_input_start_end_dates(
    loan_created, db, params, mock_is_item_available
):
    """Test checkout start and end dates are set as input."""
    start_date = "2018-02-01T09:30:00+02:00"
    end_date = "2018-02-10T09:30:00+02:00"
    loan = current_circulation.circulation.trigger(
        loan_created,
        **dict(
            params,
            start_date=start_date,
            end_date=end_date,
            trigger="checkout",
        )
    )
    db.session.commit()
    assert loan["state"] == "ITEM_ON_LOAN"
    assert loan["start_date"] == start_date
    assert loan["end_date"] == end_date


def test_checkout_fails_when_wrong_dates(
    loan_created, params, mock_is_item_available
):
    """Test checkout fails when wrong input dates."""
    with pytest.raises(ValueError):
        current_circulation.circulation.trigger(
            loan_created,
            **dict(
                params,
                start_date="2018-xx",
                end_date="2018-xx",
                trigger="checkout",
            )
        )


def test_checkout_fails_when_duration_invalid(
    loan_created, params, mock_is_item_available
):
    """Test checkout fails when wrong max duration."""
    with pytest.raises(TransitionConstraintsViolation):
        with SwappedNestedConfig(
            ["CIRCULATION_POLICIES", "checkout", "duration_validate"],
            lambda x: False,
        ):
            current_circulation.circulation.trigger(
                loan_created,
                **dict(
                    params,
                    start_date="2018-02-01T09:30:00+02:00",
                    end_date="2018-04-10T09:30:00+02:00",
                    trigger="checkout",
                )
            )


@mock.patch(
    "invenio_circulation.transitions.transitions"
    ".get_pending_loans_by_doc_pid"
)
def test_checkin_end_date_is_transaction_date(
    mock_pending_loans_for_document,
    loan_created,
    db,
    params,
    mock_is_item_available,
):
    """Test date the checkin date is the transaction date."""
    mock_pending_loans_for_document.return_value = []
    loan = current_circulation.circulation.trigger(
        loan_created,
        **dict(
            params,
            start_date="2018-02-01T09:30:00+02:00",
            end_date="2018-02-10T09:30:00+02:00",
            trigger="checkout",
        )
    )
    db.session.commit()
    assert loan["state"] == "ITEM_ON_LOAN"

    same_location = params["transaction_location_pid"]
    with SwappedConfig(
        "CIRCULATION_ITEM_LOCATION_RETRIEVER", lambda x: same_location
    ):
        params["transaction_date"] = "2018-03-11T19:15:00+02:00"
        loan = current_circulation.circulation.trigger(loan, **dict(params))
        assert loan["state"] == "ITEM_RETURNED"
        assert loan["end_date"] == params["transaction_date"]


def test_item_availibility(indexed_loans):
    """Test item_availibility with various conditions."""
    assert not is_item_available(item_pid="item_pending_1")
    assert not is_item_available(item_pid="item_on_loan_2")
    assert is_item_available(item_pid="item_returned_3")
    assert not is_item_available(item_pid="item_in_transit_4")
    assert not is_item_available(item_pid="item_at_desk_5")
    assert not is_item_available(item_pid="item_pending_on_loan_6")
    assert is_item_available(item_pid="item_returned_6")
    assert is_item_available(item_pid="no_loan")


def test_checkout_on_unavailable_item(
    loan_created, db, params, mock_is_item_available
):
    """Test checkout fails on unvailable item."""
    mock_is_item_available.return_value = False

    with pytest.raises(ItemNotAvailable):
        loan = current_circulation.circulation.trigger(
            loan_created, **dict(params, trigger="checkout")
        )

        loan_created["state"] = "ITEM_AT_DESK"

        loan = current_circulation.circulation.trigger(
            loan_created, **dict(params)
        )


@mock.patch("invenio_circulation.api.is_item_available")
def test_request_on_document_with_available_items(
    mock_available_item, loan_created, db, params
):
    """Test loan request action."""
    mock_available_item.return_value = True
    with SwappedConfig(
        "CIRCULATION_ITEMS_RETRIEVER_FROM_DOCUMENT", lambda x: ["item_pid"]
    ):
        loan = current_circulation.circulation.trigger(
            loan_created,
            **dict(
                params,
                trigger="request",
                item_pid=None,
                document_pid="document_pid",
                pickup_location_pid="pickup_location_pid",
            )
        )
        db.session.commit()
        assert loan["state"] == "PENDING"
        assert loan["item_pid"] == "item_pid"
        assert loan["document_pid"] == "document_pid"


@mock.patch("invenio_circulation.api.is_item_available")
def test_request_on_document_with_unavailable_items(
    mock_available_item, loan_created, db, params
):
    """Test loan request action."""
    mock_available_item.return_value = False
    with SwappedConfig(
        "CIRCULATION_ITEMS_RETRIEVER_FROM_DOCUMENT", lambda x: ["item_pid"]
    ):
        # remove item_pid
        params.pop("item_pid")
        loan = current_circulation.circulation.trigger(
            loan_created,
            **dict(
                params,
                trigger="request",
                document_pid="document_pid",
                pickup_location_pid="pickup_location_pid",
            )
        )
        db.session.commit()
        assert loan["state"] == "PENDING"
        assert "item_pid" not in loan
        assert loan["document_pid"] == "document_pid"


@mock.patch(
    "invenio_circulation.transitions.transitions"
    ".get_pending_loans_by_doc_pid"
)
@mock.patch("invenio_circulation.api.is_item_available")
def test_document_requests_on_item_returned(
    mock_available_item,
    mock_pending_loans_for_document,
    mock_is_item_available,
    loan_created,
    db,
    params,
):
    """Test loan request action."""

    # return item is not available
    mock_available_item.return_value = False

    with SwappedConfig(
        "CIRCULATION_DOCUMENT_RETRIEVER_FROM_ITEM", lambda x: "document_pid"
    ):
        same_location = params["transaction_location_pid"]
        with SwappedConfig(
            "CIRCULATION_ITEM_LOCATION_RETRIEVER", lambda x: same_location
        ):
            # start a loan on item with pid 'item_pid'
            new_loan = current_circulation.circulation.trigger(
                loan_created,
                **dict(
                    params,
                    trigger="checkout",
                    item_pid="item_pid",
                    pickup_location_pid="pickup_location_pid",
                )
            )
            db.session.commit()
            assert new_loan["state"] == "ITEM_ON_LOAN"

            # create a new loan request on document_pid without items available
            new_loan_created = Loan.create({
                Loan.pid_field: "2"
            })
            # remove item_pid
            params.pop("item_pid")
            pending_loan = current_circulation.circulation.trigger(
                new_loan_created,
                **dict(
                    params,
                    trigger="request",
                    document_pid="document_pid",
                    pickup_location_pid="pickup_location_pid",
                )
            )
            db.session.commit()
            assert pending_loan["state"] == "PENDING"
            # no item available found. Request is created with no item attached
            assert "item_pid" not in pending_loan
            assert pending_loan["document_pid"] == "document_pid"

            # resolve pending document requests to `document_pid`
            mock_pending_loans_for_document.return_value = [pending_loan]

            returned_loan = current_circulation.circulation.trigger(
                new_loan,
                **dict(
                    params,
                    item_pid="item_pid",
                    pickup_location_pid="pickup_location_pid",
                )
            )
            db.session.commit()
            assert returned_loan["state"] == "ITEM_RETURNED"

            # item `item_pid` has been attached to pending loan request on
            # `document_pid` automatically
            assert pending_loan["state"] == "PENDING"
            assert pending_loan["item_pid"] == "item_pid"
            assert pending_loan["document_pid"] == "document_pid"
