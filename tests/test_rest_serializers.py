# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CERN.
# Copyright (C) 2019 RERO.
#
# Invenio-Circulation is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

from __future__ import absolute_import, print_function

import json
from datetime import timedelta

import arrow
import pytest
from flask import url_for


def test_rest_loader_valid_params(app, json_headers):
    """Test rest loader and serializer with valid params."""

    with app.test_client() as client:
        url = url_for("invenio_records_rest.loanid_list")

        now = arrow.utcnow()
        start_date = now + timedelta(days=1)
        end_date = now + timedelta(days=30)
        params = dict(
            document_pid="document_pid",
            item_pid=dict(type="itemid", value="1"),
            patron_pid="patron_pid",
            transaction_date=now.isoformat(),
            transaction_location_pid="loc_pid",
            transaction_user_pid="user_pid",
            start_date=start_date.date().isoformat(),
            end_date=end_date.date().isoformat()
        )
        res = client.post(
            url, data=json.dumps(params), headers=json_headers
        )
        assert res.status_code == 201
        loan = res.get_json()
        assert loan['metadata']['transaction_date'] == now.isoformat()

        url = url_for("invenio_records_rest.loanid_item", pid_value='1')
        res = client.get(url, headers=json_headers)
        assert res.status_code == 200
        loan = res.get_json()
        assert loan['metadata']['transaction_date'] == now.isoformat()


@pytest.mark.parametrize(
    "invalid_params",
    [
        {"transaction_date": arrow.utcnow().format('YYYY-MM-DD')},
        {"transaction_date": arrow.utcnow().to('US/Pacific').isoformat()},
        {"start_date": arrow.utcnow().isoformat()},
        {"end_date": arrow.utcnow().isoformat()},
        {"request_expire_date": arrow.utcnow().isoformat()},
        {"item_pid": dict(value="1")},
        {"item_pid": dict(type="itemid")}
    ]
)
def test_rest_loader_invalid_transaction_date_format(
    app, json_headers, invalid_params
):
    """Test rest loader transaction_date format validation."""

    with app.test_client() as client:
        url = url_for("invenio_records_rest.loanid_list")

        params = dict(
            patron_pid="patron_pid",
            transaction_location_pid="loc_pid",
            transaction_user_pid="user_pid",
            **invalid_params
        )
        res = client.post(
            url, data=json.dumps(params), headers=json_headers
        )
        assert res.status_code == 400
        response = res.get_json()
        assert response['message'] == "Validation error."
