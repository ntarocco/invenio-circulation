# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 CERN.
# Copyright (C) 2018 RERO.
#
# Invenio-Circulation is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Tests for loan states."""

import json

from flask import url_for

from invenio_circulation.api import Loan
from invenio_circulation.pid.fetchers import loan_pid_fetcher
from invenio_circulation.pid.minters import loan_pid_minter
from invenio_circulation.proxies import current_circulation
from invenio_circulation.views import HTTP_CODES, build_url_action_for_pid


def test_api_get_loan(app, db, json_headers):
    """Test API GET call to fetch a loan by PID."""
    loan = Loan.create({})
    minted_loan = loan_pid_minter(loan.id, loan)
    db.session.commit()

    loan_pid = loan_pid_fetcher(loan.id, loan)
    assert minted_loan.pid_value == loan_pid.pid_value

    with app.test_client() as client:
        url = url_for('invenio_records_rest.loanid_item',
                      pid_value=loan_pid.pid_value)
        res = client.get(url, headers=json_headers)
        assert res.status_code == 200
        loan_dict = json.loads(res.data.decode('utf-8'))
        assert loan_dict['metadata']['state'] == loan['state']


def test_api_explicit_loan_valid_action(app, db, json_headers, params,
                                        mock_is_item_available):
    """Test API valid action on loan."""
    loan = Loan.create({})
    minted_loan = loan_pid_minter(loan.id, loan)
    db.session.commit()

    loan_pid = loan_pid_fetcher(loan.id, loan)
    assert minted_loan.pid_value == loan_pid.pid_value

    with app.test_client() as client:
        url = url_for('invenio_circulation.loanid_actions',
                      pid_value=loan_pid.pid_value, action='checkout')
        res = client.post(url, headers=json_headers, data=json.dumps(params))
        assert res.status_code == HTTP_CODES['accepted']
        loan_dict = json.loads(res.data.decode('utf-8'))
        assert loan_dict['metadata']['state'] == 'ITEM_ON_LOAN'


def test_api_automatic_loan_valid_action(app, db, json_headers, params):
    """Test API valid action on loan."""
    loan = Loan.create({})
    minted_loan = loan_pid_minter(loan.id, loan)
    loan = current_circulation.circulation.trigger(
        loan, **dict(params,
                     trigger='request',
                     pickup_location_pid='pickup_location_pid')
    )
    db.session.commit()
    assert loan['state'] == 'PENDING'

    app.config[
        'CIRCULATION_ITEM_LOCATION_RETRIEVER'
    ] = lambda x: 'pickup_location_pid'

    loan_pid = loan_pid_fetcher(loan.id, loan)
    assert minted_loan.pid_value == loan_pid.pid_value

    with app.test_client() as client:
        url = url_for('invenio_circulation.loanid_actions',
                      pid_value=loan_pid.pid_value, action='next')
        res = client.post(url, headers=json_headers, data=json.dumps(params))

        assert res.status_code == HTTP_CODES['accepted']
        loan_dict = json.loads(res.data.decode('utf-8'))
        assert loan_dict['metadata']['state'] == 'ITEM_AT_DESK'


def test_api_loan_invalid_action(app, db, json_headers, params,
                                 mock_is_item_available):
    """Test API invalid action on loan."""
    loan = Loan.create({})
    minted_loan = loan_pid_minter(loan.id, loan)

    loan = current_circulation.circulation.trigger(
        loan, **dict(params,
                     trigger='request',
                     pickup_location_pid='pickup_location_pid')
    )
    db.session.commit()
    assert loan['state'] == 'PENDING'

    loan_pid = loan_pid_fetcher(loan.id, loan)
    assert minted_loan.pid_value == loan_pid.pid_value

    with app.test_client() as client:
        url = url_for('invenio_circulation.loanid_actions',
                      pid_value=loan_pid.pid_value, action='checkout')
        res = client.post(url, headers=json_headers, data=json.dumps(params))
        assert res.status_code == HTTP_CODES['method_not_allowed']
        error_dict = json.loads(res.data.decode('utf-8'))
        assert 'message' in error_dict


def test_api_loans_links_factory(app, db, json_headers, params,
                                 mock_is_item_available):
    """Test API GET call to fetch a loan by PID."""
    loan = Loan.create({})
    minted_loan = loan_pid_minter(loan.id, loan)
    db.session.commit()
    loan_pid = loan_pid_fetcher(loan.id, loan)

    expected_links = {
        'actions': {
            'request': build_url_action_for_pid(loan_pid, 'request'),
            'checkout': build_url_action_for_pid(loan_pid, 'checkout')
        }
    }
    with app.test_client() as client:
        url = url_for('invenio_records_rest.loanid_item',
                      pid_value=loan_pid.pid_value)
        res = client.get(url, headers=json_headers)
        assert res.status_code == 200
        loan_dict = json.loads(res.data.decode('utf-8'))
        assert loan_dict['links'] == expected_links
