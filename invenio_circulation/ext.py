# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 CERN.
# Copyright (C) 2018 RERO.
#
# Invenio-Circulation is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module for the circulation of bibliographic items."""

from __future__ import absolute_import, print_function

from copy import deepcopy

from flask import current_app
from werkzeug.utils import cached_property

from . import config
from .errors import InvalidState, NoValidTransitionAvailable, \
    TransitionConditionsFailed
from .transitions.base import Transition
from .views import build_blueprint_with_loan_actions


class InvenioCirculation(object):
    """Invenio-Circulation extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.config.setdefault("RECORDS_REST_ENDPOINTS", {})

        app.config["RECORDS_REST_ENDPOINTS"].update(
            app.config["CIRCULATION_REST_ENDPOINTS"]
        )
        blueprint = build_blueprint_with_loan_actions(app)
        app.register_blueprint(blueprint)
        app.extensions["invenio-circulation"] = self

    def init_config(self, app):
        """Initialize configuration."""
        app.config.setdefault(
            "CIRCULATION_ITEMS_RETRIEVER_FROM_DOCUMENT", lambda x: []
        )
        app.config.setdefault(
            "CIRCULATION_DOCUMENT_RETRIEVER_FROM_ITEM", lambda x: None
        )
        for k in dir(config):
            if k.startswith("CIRCULATION_"):
                app.config.setdefault(k, getattr(config, k))

    @cached_property
    def circulation(self):
        """."""
        return _Circulation(
            transitions_config=deepcopy(
                current_app.config["CIRCULATION_LOAN_TRANSITIONS"]
            )
        )


class _Circulation(object):
    """."""

    def __init__(self, transitions_config):
        """."""
        self.transitions = {}
        for src_state, transitions in transitions_config.items():
            self.transitions.setdefault(src_state, [])
            for t in transitions:
                _cls = t.pop("transition", Transition)
                instance = _cls(**dict(t, src=src_state))
                self.transitions[src_state].append(instance)

    def _validate_current_state(self, current_state):
        """."""
        if not current_state or current_state not in self.transitions:
            raise InvalidState("Invalid loan state `{}`".format(current_state))

    def trigger(self, loan, **kwargs):
        """."""
        current_state = loan.get("state")
        self._validate_current_state(current_state)

        for t in self.transitions[current_state]:
            try:
                t.execute(loan, **kwargs)
                return loan
            except TransitionConditionsFailed as ex:
                current_app.logger.debug(ex.msg)
                pass

        raise NoValidTransitionAvailable(
            "No valid transition with current"
            " state `{}`.".format(current_state)
        )
