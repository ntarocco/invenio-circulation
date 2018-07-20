# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 CERN.
# Copyright (C) 2018 RERO.
#
# Invenio-Circulation is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Circulation API."""

import warnings
from datetime import datetime

from flask import current_app
from invenio_records.api import Record
from transitions import Machine

import config


class Loan(Record):
    """Loan record class."""

    def __init__(self, data, model=None):
        """."""
        self.states = current_app.config['CIRCULATION_LOAN_STATES']
        self.transitions = current_app.config['CIRCULATION_LOAN_TRANSITIONS']
        data.setdefault('state', self.states[0])
        super(Loan, self).__init__(data, model)
        Machine(model=self, states=self.states, send_event=True,
                transitions=self.transitions,
                initial=self['state'],
                finalize_event='save')

    def set_request_parameters(self, event):
        """."""
        self.set_parameters(event)
        self['pickup_location_pid'] = event.kwargs.get('pickup_location_pid')

    def set_parameters(self, event):
        """."""
        params = event.kwargs
        self['transaction_user_pid'] = params.get('transaction_user_pid')
        self['patron_pid'] = params.get('patron_pid')
        self['item_pid'] = params.get('item_pid')
        self['transaction_location_pid'] = params.get(
            'transaction_location_pid')
        self['transaction_date'] = params.get('transaction_date',
                                              datetime.now().isoformat())

    def is_pickup_at_same_library(self, event):
        """."""
        item_location_pid = current_app.config.get(
            'CIRCULATION_ITEM_LOCATION_RETRIEVER')(self['item_pid'])
        return self['pickup_location_pid'] == item_location_pid

    @property
    def policies(self):
        """."""
        return current_app.config.get('CIRCULATION_POLICIES')

    def is_checkout_valid(self, event):
        """."""
        dates = self.policies['checkout'](**event.kwargs)
        if not dates:
            return False
        self['start_date'], self['end_date'] = dates
        return True

    def save(self, event):
        """."""
        if event.error:
            raise Exception(event.error)
        else:
            self['state'] = self.state
            self.commit()

    @classmethod
    def export_diagram(cls, output_file):
        """."""
        from transitions.extensions import GraphMachine

        try:
            import pygraphviz
        except ImportError:
            warnings.warn('dependency not found, please install pygraphviz to '
                          'export the circulation state diagram.')
            return False

        # FIXME: replace config with current_app.config when CLI has appcontext
        # states = current_app.config['CIRCULATION_LOAN_STATES']
        # transitions = current_app.config['CIRCULATION_LOAN_TRANSITIONS']
        states = config.CIRCULATION_LOAN_STATES
        transitions = config.CIRCULATION_LOAN_TRANSITIONS
        m = GraphMachine(states=states, transitions=transitions,
                         initial=states[0], show_conditions=True,
                         title='Circulation State Diagram')
        m.get_graph().draw(output_file, prog='dot')
        return True
