# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CERN.
# Copyright (C) 2019 RERO.
#
# Invenio-Circulation is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Circulation Patron JSON Resolver module."""

import jsonresolver
from werkzeug.routing import Rule


@jsonresolver.hookimpl
def jsonresolver_loader(url_map):
    """Resolve the patron reference."""
    from flask import current_app as app
    resolving_path = app.config.get("CIRCULATION_PATRON_RESOLVING_PATH") or "/"
    url_map.add(Rule(
        resolving_path,
        endpoint=app.config.get('CIRCULATION_PATRON_RESOLVER_ENDPOINT'),
        host=app.config.get('JSONSCHEMAS_HOST')))
