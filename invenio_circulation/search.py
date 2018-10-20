# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 CERN.
# Copyright (C) 2018 RERO.
#
# Invenio-Circulation is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Search utilities."""

from elasticsearch_dsl.query import Bool, Q
from invenio_search.api import RecordsSearch


class LoansSearch(RecordsSearch):
    """RecordsSearch for borrowed documents."""

    class Meta:
        """Search only on loans index."""

        index = "loans"
        doc_types = None

    @classmethod
    def search_loans_by_pid(cls, item_pid=None, document_pid=None,
                            filter_states=None, exclude_states=None):
        """Retrieve loans attached to the given item or document."""
        search = cls()

        if filter_states:
            search = search.query(
                Bool(filter=[Q("terms", state=filter_states)])
            )
        elif exclude_states:
            search = search.query(
                Bool(filter=[~Q("terms", state=exclude_states)])
            )

        if document_pid:
            search = search.filter("term", document_pid=document_pid)
        elif item_pid:
            search = search.filter("term", item_pid=item_pid)
        else:
            raise ValueError("Must specify item_pid or document_pid param")

        for result in search.scan():
            yield result

    @classmethod
    def search_loans_by_patron_pid(cls, patron_pid):
        """Retrieve loans of a patron."""
        search = cls()
        search = search.filter("term", patron_pid=patron_pid)
        for result in search.scan():
            yield result
