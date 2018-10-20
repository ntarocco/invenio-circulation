# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 CERN.
# Copyright (C) 2018 RERO.
#
# Invenio-Circulation is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration."""

from __future__ import absolute_import, print_function

import json
import uuid
from os.path import dirname, join

import mock
import pytest
from invenio_access import ActionRoles, superuser_access
from invenio_accounts.models import Role
from invenio_app.factory import create_api
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_records_rest.utils import allow_all
from invenio_search import current_search

from invenio_circulation.api import Loan
from invenio_circulation.permissions import loan_access
from invenio_circulation.pidstore.minters import loan_pid_minter

from .helpers import create_loan, test_views_permissions_factory


@pytest.fixture(scope='module')
def create_app():
    """Return API app."""
    return create_api


@pytest.fixture(scope="module")
def app_config(app_config):
    """Flask application fixture."""
    app_config["JSONSCHEMAS_ENDPOINT"] = "/schema"
    app_config["JSONSCHEMAS_HOST"] = "localhost:5000"
    app_config["RECORDS_REST_DEFAULT_READ_PERMISSION_FACTORY"] = allow_all
    app_config["CIRCULATION_ITEM_EXISTS"] = lambda x: True
    app_config["CIRCULATION_PATRON_EXISTS"] = lambda x: True
    return app_config


@pytest.fixture()
def loan_created(app):
    """Minimal Loan object."""
    record_uuid = uuid.uuid4()
    new_loan = {}
    loan_pid_minter(record_uuid, data=new_loan)
    loan = Loan.create(data=new_loan, id_=record_uuid)
    db.session.commit()
    yield loan


@pytest.fixture()
def params():
    """Common API REST payload."""
    return dict(
        transaction_user_pid="user_pid",
        patron_pid="patron_pid",
        item_pid="item_pid",
        transaction_location_pid="loc_pid",
        transaction_date="2018-02-01T09:30:00+02:00",
    )


@pytest.fixture()
def json_headers(app):
    """JSON headers."""
    return [
        ("Content-Type", "application/json"),
        ("Accept", "application/json"),
    ]


@pytest.fixture(scope="session")
def test_data():
    """Load test records."""
    path = "data/loans.json"
    with open(join(dirname(__file__), path)) as fp:
        loans = json.load(fp)
    yield loans


@pytest.fixture()
def test_loans(db, test_data):
    """Load test records."""
    loans = []
    for data in test_data:
        loans.append(create_loan(data))
    db.session.commit()
    yield loans


@pytest.fixture()
def indexed_loans(es, test_loans):
    """Get a function to wait for records to be flushed to index."""
    indexer = RecordIndexer()
    for pid, loan in test_loans:
        indexer.index(loan)
    current_search.flush_and_refresh(index="loans")

    yield test_loans

    for pid, loan in test_loans:
        indexer.delete_by_id(loan.id)
    current_search.flush_and_refresh(index="loans")


@pytest.fixture()
def mock_is_item_available():
    """Mock item_available check."""
    path = "invenio_circulation.transitions.base.is_item_available"
    with mock.patch(path) as mock_is_item_available:
        mock_is_item_available.return_value = True
        yield mock_is_item_available


@pytest.fixture()
def users(db, base_app):
    """Create admin, manager and user."""
    base_app.config["CIRCULATION_VIEWS_PERMISSIONS_FACTORY"] = \
        test_views_permissions_factory

    with db.session.begin_nested():
        datastore = base_app.extensions['security'].datastore

        # create users
        manager = datastore.create_user(email='manager@test.com',
                                        password='123456', active=True)
        admin = datastore.create_user(email='admin@test.com',
                                      password='123456', active=True)
        user = datastore.create_user(email='user@test.com',
                                     password='123456', active=True)

        # Give role to admin
        admin_role = Role(name='admin')
        db.session.add(ActionRoles(action=superuser_access.value,
                                   role=admin_role))
        datastore.add_role_to_user(admin, admin_role)
        # Give role to user
        manager_role = Role(name='manager')
        db.session.add(ActionRoles(action=loan_access.value,
                                   role=manager_role))
        datastore.add_role_to_user(manager, manager_role)
    db.session.commit()

    return {
        'admin': admin,
        'manager': manager,
        'user': user,
    }
