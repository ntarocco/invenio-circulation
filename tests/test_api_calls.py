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
from invenio_circulation.pid.fetchers import loanid_fetcher
from invenio_circulation.pid.minters import loanid_minter
from invenio_circulation.views import HTTP_CODES


def test_api_get_loan(app, db, json_headers):
    """Test API GET call to fetch a loan by PID."""
    loan = Loan.create({})
    minted_loan = loanid_minter(loan.id, loan)
    db.session.commit()

    loan_pid = loanid_fetcher(loan.id, loan)
    assert minted_loan.pid_value == loan_pid.pid_value

    with app.test_client() as client:
        url = url_for('invenio_records_rest.loanid_item',
                      pid_value=loan_pid.pid_value)
        res = client.get(url, headers=json_headers)
        assert res.status_code == 200
        loan_dict = json.loads(res.data.decode('utf-8'))
        assert loan_dict['metadata']['state'] == loan['state']


def test_api_loan_valid_action(app, db, json_headers, params):
    """Test API valid action on loan."""
    loan = Loan.create({})
    minted_loan = loanid_minter(loan.id, loan)
    db.session.commit()

    loan_pid = loanid_fetcher(loan.id, loan)
    assert minted_loan.pid_value == loan_pid.pid_value

    with app.test_client() as client:
        url = url_for('invenio_circulation.loanid_actions',
                      pid_value=loan_pid.pid_value, action='checkout')
        res = client.post(url, headers=json_headers, data=json.dumps(params))
        assert res.status_code == HTTP_CODES['accepted']
        loan_dict = json.loads(res.data.decode('utf-8'))
        assert loan_dict['metadata']['state'] == 'ITEM_ON_LOAN'


def test_api_loan_invalid_action(app, db, json_headers, params):
    """Test API invalid action on loan."""
    loan = Loan.create({})
    minted_loan = loanid_minter(loan.id, loan)
    db.session.commit()

    loan_pid = loanid_fetcher(loan.id, loan)
    assert minted_loan.pid_value == loan_pid.pid_value

    with app.test_client() as client:
        url = url_for('invenio_circulation.loanid_actions',
                      pid_value=loan_pid.pid_value, action='validate_request')
        res = client.post(url, headers=json_headers, data=json.dumps(params))
        assert res.status_code == HTTP_CODES['method_not_allowed']
        error_dict = json.loads(res.data.decode('utf-8'))
        assert 'message' in error_dict
