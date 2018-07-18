# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 CERN.
# Copyright (C) 2018 RERO.
#
# Invenio-Circulation is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module for the circulation of bibliographic items."""

from __future__ import absolute_import, print_function

from . import config


class InvenioCirculation(object):
    """Invenio-Circulation extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.config.setdefault('RECORDS_REST_ENDPOINTS', {})
        app.config['RECORDS_REST_ENDPOINTS'].update(
            app.config['CIRCULATION_REST_ENDPOINTS'])
        app.extensions['invenio-circulation'] = self

    def init_config(self, app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith('CIRCULATION_'):
                app.config.setdefault(k, getattr(config, k))
