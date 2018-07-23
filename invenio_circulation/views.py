from copy import deepcopy
from functools import wraps

from flask import Blueprint, request, current_app
from functools import partial
from invenio_db import db
from invenio_records_rest.views import pass_record, create_error_handlers as \
    records_rest_error_handlers, need_record_permission, \
    verify_record_permission
from invenio_records_rest.utils import obj_or_import_string, deny_all
from invenio_rest import ContentNegotiatedMethodView
from invenio_rest.views import create_api_errorhandler
from transitions import MachineError

from invenio_circulation.errors import LoanActionError
from invenio_circulation.proxies import current_circulation

HTTP_CODES = {
    'method_not_allowed': 405,
    'accepted': 202
}


def create_error_handlers(blueprint):
    """Create error handlers on blueprint."""
    blueprint.errorhandler(LoanActionError)(create_api_errorhandler(
        status=HTTP_CODES['method_not_allowed'], message='Invalid loan action'
    ))
    records_rest_error_handlers(blueprint)


def build_blueprint_with_loan_actions(app):
    """."""
    blueprint = Blueprint(
        'invenio_circulation',
        __name__,
        url_prefix='',
    )
    create_error_handlers(blueprint)

    endpoints = app.config.get('CIRCULATION_REST_ENDPOINTS', [])
    transitions = app.config.get('CIRCULATION_LOAN_TRANSITIONS', [])

    for endpoint, options in (endpoints or {}).items():
        options = deepcopy(options)

        if 'record_serializers' in options:
            serializers = options.get('record_serializers')
            serializers = {mime: obj_or_import_string(func)
                           for mime, func in serializers.items()}
        else:
            serializers = {}

        ctx = dict(
            read_permission_factory=obj_or_import_string(
                options.get('read_permission_factory_imp')
            ),
            create_permission_factory=obj_or_import_string(
                options.get('create_permission_factory_imp')
            ),
            update_permission_factory=obj_or_import_string(
                options.get('update_permission_factory_imp')
            ),
            delete_permission_factory=obj_or_import_string(
                options.get('delete_permission_factory_imp')
            ),
        )

        loan_actions = LoanActionResource.as_view(
            LoanActionResource.view_name.format(endpoint),
            serializers=serializers,
            ctx=ctx,
        )

        distinct_actions = (transition['trigger'] for transition in
                            transitions)
        url = '{0}/<any({1}):action>'.format(
                options['item_route'],
                ','.join(distinct_actions),
            )
        blueprint.add_url_rule(
            url,
            view_func=loan_actions,
            methods=['POST'],
        )

        return blueprint


def need_record_action_permission(f):
    @wraps(f)
    def inner(self, pid, record, action, **kwargs):
        factory = current_circulation.action_permission_factories.get(
            request.view_args['action'], deny_all)
        verify_record_permission(factory, record)
        return f(self, pid, record, action, **kwargs)
    return inner


class LoanActionResource(ContentNegotiatedMethodView):
    """Loan action resource."""

    view_name = '{0}_actions'

    def __init__(self, serializers, ctx, *args, **kwargs):
        """Constructor."""
        super(LoanActionResource, self).__init__(
            serializers,
            default_media_type=ctx.get('default_media_type'),
            *args,
            **kwargs
        )
        for key, value in ctx.items():
            setattr(self, key, value)
        for key, value in current_circulation.action_permission_factories.items():
            setattr(self, key, value)

    @pass_record
    @need_record_action_permission
    def post(self, pid, record, action, **kwargs):
        """Handle loan action."""
        params = request.get_json()

        try:
            # perform action on the current loan
            getattr(record, action)(**params)
            db.session.commit()
        except MachineError as ex:
            current_app.logger.exception(ex)
            raise LoanActionError(ex)

        return self.make_response(pid, record, HTTP_CODES['accepted'])
