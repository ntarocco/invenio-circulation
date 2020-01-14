# -*- coding: utf-8 -*-
#
# Copyright (C) 2018-2020 CERN.
# Copyright (C) 2018-2020 RERO.
#
# Invenio-Circulation is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Circulation views."""

from copy import deepcopy

from flask import Blueprint, current_app, request, url_for
from invenio_db import db
from invenio_records_rest.utils import obj_or_import_string
from invenio_records_rest.views import pass_record
from invenio_rest import ContentNegotiatedMethodView

from .errors import InvalidLoanStateError, ItemNotAvailableError, \
    MissingRequiredParameterError
from .permissions import need_permissions
from .pidstore.pids import _LOANID_CONVERTER, CIRCULATION_LOAN_PID_TYPE
from .proxies import current_circulation
from .records.loaders import loan_loader, loan_replace_item_loader
from .signals import loan_replace_item


def extract_transitions_from_app(app):
    """Return all possible actions for configured transitions."""
    transitions_config = app.config.get("CIRCULATION_LOAN_TRANSITIONS", {})
    distinct_actions = set()
    for src_state, transitions in transitions_config.items():
        for t in transitions:
            distinct_actions.add(t.get("trigger", "next"))
    return distinct_actions


def build_url_action_for_pid(pid, action):
    """Build urls for Loan actions."""
    return url_for(
        "invenio_circulation_loan_actions.{0}_actions".format(pid.pid_type),
        pid_value=pid.pid_value,
        action=action,
        _external=True,
    )


def _get_loan_endpoint_options(app):
    """Return the configured endpoint options."""
    endpoints = app.config.get("CIRCULATION_REST_ENDPOINTS", [])
    options = deepcopy(endpoints.get(CIRCULATION_LOAN_PID_TYPE, {}))
    default_media_type = options.get("default_media_type", "")
    rec_serializers = options.get("record_serializers", {})
    serializers = {
        mime: obj_or_import_string(func)
        for mime, func in rec_serializers.items()
    }
    return (
        options,
        dict(
            serializers=serializers,
            default_media_type=default_media_type,
            ctx={},
        ),
    )


def create_loan_actions_blueprint(app):
    """Create a blueprint for Loan actions."""
    blueprint = Blueprint(
        "invenio_circulation_loan_actions", __name__, url_prefix=""
    )

    all_options, view_options = _get_loan_endpoint_options(app)
    view_options["ctx"]["loader"] = loan_loader
    loan_actions = LoanActionResource.as_view(
        LoanActionResource.view_name.format(CIRCULATION_LOAN_PID_TYPE),
        **view_options
    )

    distinct_actions = extract_transitions_from_app(app)
    url = "{0}/<any({1}):action>".format(
        all_options["item_route"], ",".join(distinct_actions)
    )

    blueprint.add_url_rule(url, view_func=loan_actions, methods=["POST"])
    return blueprint


class LoanActionResource(ContentNegotiatedMethodView):
    """Loan action resource."""

    view_name = "{0}_actions"

    def __init__(self, serializers, ctx, *args, **kwargs):
        """Constructor."""
        super().__init__(serializers, *args, **kwargs)
        for key, value in ctx.items():
            setattr(self, key, value)

    @need_permissions("loan-actions")
    @pass_record
    def post(self, pid, record, action, **kwargs):
        """Handle loan action."""
        data = self.loader()
        record = current_circulation.circulation.trigger(
            record, **dict(data, trigger=action)
        )
        db.session.commit()
        return self.make_response(
            pid,
            record,
            202,
            links_factory=current_app.config.get(
                "CIRCULATION_LOAN_LINKS_FACTORY"
            ),
        )


def create_loan_replace_item_blueprint(app):
    """Create a blueprint for replacing Loan Item."""
    blueprint = Blueprint(
        "invenio_circulation_loan_replace_item", __name__, url_prefix=""
    )

    _, view_options = _get_loan_endpoint_options(app)
    view_options["ctx"]["loader"] = loan_replace_item_loader
    replace_item_view = LoanReplaceItemResource.as_view(
        LoanReplaceItemResource.view_name.format(CIRCULATION_LOAN_PID_TYPE),
        **view_options
    )

    url = "circulation/loans/<{0}:pid_value>/replace-item".format(
        _LOANID_CONVERTER
    )
    blueprint.add_url_rule(url, view_func=replace_item_view, methods=["POST"])
    return blueprint


def validate_replace_item(loan, new_item_pid):
    """Validate the new item before replacing the item of the loan.

    :param loan: the current loan to modify.
    :param new_item_pid: a dict containing `value` and `type` fields to
        uniquely identify the item.
    """
    active_states = current_app.config["CIRCULATION_STATES_LOAN_ACTIVE"]
    if loan["state"] not in active_states:
        raise InvalidLoanStateError(
            description=(
                "Cannot replace item in a loan that is not in active state. "
                "Current loan state '{}'".format(loan["state"])
            )
        )

    if not new_item_pid:
        raise MissingRequiredParameterError(
            description="Parameter 'new_item_pid' is required."
        )

    item_exists_func = current_app.config["CIRCULATION_ITEM_EXISTS"]
    if not item_exists_func(new_item_pid):
        raise ItemNotAvailableError(item_pid=new_item_pid)


class LoanReplaceItemResource(ContentNegotiatedMethodView):
    """Loan update resource."""

    view_name = "loan_replace_item_resource"

    def __init__(self, serializers, ctx, *args, **kwargs):
        """Constructor."""
        super().__init__(serializers, *args, **kwargs)
        for key, value in ctx.items():
            setattr(self, key, value)

    @need_permissions("loan-actions")
    @pass_record
    def post(self, pid, record, *args, **kwargs):
        """Handle POST request to update loan with new item."""
        data = self.loader()
        old_item_pid = record.get("item_pid")
        new_item_pid = data.get("item_pid")

        validate_replace_item(record, new_item_pid)
        record.update_item_ref(new_item_pid)

        record.commit()
        db.session.commit()
        current_circulation.loan_indexer().index(record)

        if old_item_pid:
            loan_replace_item.send(self, old_item_pid=old_item_pid,
                                   new_item_pid=new_item_pid)

        return self.make_response(
            pid,
            record,
            202,
            links_factory=current_app.config.get(
                "CIRCULATION_LOAN_LINKS_FACTORY"
            ),
        )
