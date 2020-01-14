# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2020 CERN.
# Copyright (C) 2019-2020 RERO.
#
# invenio-circulation is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Circulation record loaders module."""

from invenio_records_rest.loaders import marshmallow_loader

from .schemas.json import LoanReplaceItemSchemaV1, LoanSchemaV1

loan_loader = marshmallow_loader(LoanSchemaV1)
loan_replace_item_loader = marshmallow_loader(LoanReplaceItemSchemaV1)
