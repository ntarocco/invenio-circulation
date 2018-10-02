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
from os.path import dirname, join

import mock
import pytest
from flask import Flask
from helpers import create_loan
from invenio_db.ext import InvenioDB
from invenio_indexer import InvenioIndexer
from invenio_indexer.api import RecordIndexer
from invenio_jsonschemas import InvenioJSONSchemas
from invenio_pidstore.ext import InvenioPIDStore
from invenio_records.ext import InvenioRecords
from invenio_records_rest.ext import InvenioRecordsREST
from invenio_records_rest.utils import PIDConverter
from invenio_records_rest.views import create_blueprint_from_app
from invenio_search import InvenioSearch, current_search

from invenio_circulation.api import Loan
from invenio_circulation.ext import InvenioCirculation


@pytest.fixture(scope="module")
def app_config(app_config):
    """Flask application fixture."""
    app_config["SERVER_NAME"] = "localhost:5000"
    app_config["JSONSCHEMAS_ENDPOINT"] = "/schema"
    app_config["JSONSCHEMAS_HOST"] = "localhost:5000"
    app_config["RECORDS_REST_DEFAULT_READ_PERMISSION_FACTORY"] = None
    app_config["CIRCULATION_ITEM_EXISTS"] = lambda x: True
    app_config["CIRCULATION_PATRON_EXISTS"] = lambda x: True
    return app_config


@pytest.fixture(scope="module")
def create_app():
    """Flask application fixture."""
    def _create_app(**kwargs):
        app = Flask("test")
        app.config.update(kwargs)
        return app

    return _create_app


@pytest.fixture(scope="module")
def base_app(base_app):
    """Flask base application fixture."""
    base_app.url_map.converters["pid"] = PIDConverter
    InvenioDB(base_app)
    InvenioRecords(base_app)
    InvenioRecordsREST(base_app)
    InvenioPIDStore(base_app)
    InvenioIndexer(base_app)
    InvenioPIDStore(base_app)
    InvenioSearch(base_app)
    InvenioCirculation(base_app)
    InvenioJSONSchemas(base_app)
    base_app.register_blueprint(create_blueprint_from_app(base_app))
    yield base_app


@pytest.yield_fixture()
def loan_created(db):
    """Minimal Loan object."""
    yield Loan.create({})


@pytest.fixture()
def params():
    """."""
    return dict(
        transaction_user_pid="user_pid",
        patron_pid="patron_pid",
        item_pid="item_pid",
        transaction_location_pid="loc_pid",
        transaction_date="2018-02-01T09:30:00+02:00",
    )


@pytest.yield_fixture()
def loan_schema():
    """Loan Json schema."""
    yield {"$schema": "http://localhost:5000/schema/loans/loan-v1.0.0.json"}


@pytest.fixture()
def json_headers(app):
    """JSON headers."""
    return [
        ("Content-Type", "application/json"),
        ("Accept", "application/json"),
    ]


@pytest.yield_fixture(scope="session")
def test_data():
    """Load test records."""
    path = "data/loans.json"
    with open(join(dirname(__file__), path)) as fp:
        loans = json.load(fp)
    yield loans


@pytest.yield_fixture()
def test_loans(db, test_data):
    """Load test records."""
    loans = []
    for data in test_data:
        loans.append(create_loan(data))
    db.session.commit()
    yield loans


@pytest.yield_fixture()
def indexer(base_app, es):
    """Create a record indexer."""
    yield RecordIndexer()


@pytest.yield_fixture()
def indexed_loans(indexer, test_loans):
    """Get a function to wait for records to be flushed to index."""
    for pid, loan in test_loans:
        indexer.index_by_id(loan.id)
    current_search.flush_and_refresh(index="loans")

    yield test_loans

    for pid, loan in test_loans:
        indexer.delete_by_id(loan.id)
    current_search.flush_and_refresh(index="loans")


@pytest.yield_fixture()
def mock_is_item_available():
    """Mock item_available check."""
    path = "invenio_circulation.transitions.base.is_item_available"
    with mock.patch(path) as mock_is_item_available:
        mock_is_item_available.return_value = True
        yield mock_is_item_available
