# -*- coding: utf-8 -*-
#
# Copyright (C) 2018-2020 CERN.
# Copyright (C) 2018-2020 RERO.
#
# Invenio-Circulation is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Invenio Circulation transitions conditions."""

from flask import current_app


def is_same_location(item_pid, input_location_pid):
    """Return True if item belonging location is same as input parameter.

    :param item_pid: a dict containing `value` and `type` fields to
        uniquely identify the item.
    """
    item_location_pid = current_app.config[
        "CIRCULATION_ITEM_LOCATION_RETRIEVER"
    ](item_pid)
    return input_location_pid == item_location_pid
