import logging

from django.contrib.sessions.backends.db import SessionStore
from django.core.exceptions import ValidationError
from saleor.core.jwt import create_access_token, create_refresh_token

import yaml
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.handlers.wsgi import WSGIRequest
from django.middleware.csrf import _get_new_csrf_token

from social_django.strategy import DjangoStrategy
from social_django.views import _do_login
from social_core.utils import get_strategy

from saleor.plugins.base_plugin import BasePlugin, ConfigurationTypeField, ExternalAccessTokens
from . import (
    CONFIG_CODE,
    DEFAULT_BACKEND_CODE,
    EXCHANGE_REDIRECT_URI_CODE,
    SOCIAL_STRATEGY_CODE,
    SOCIAL_STORAGE_CODE,
)

from .utils import (
    do_auth,
    do_complete,
    validate_storefront_redirect_url,
)

logger = logging.getLogger(__name__)

class SocialAuthPlugin(BasePlugin):
    PLUGIN_ID = 'tinaam.authentication.SocialAuthPlugin'
    PLUGIN_NAME = "Social Auth"
    # auth external auth plugin should be global plugin
    CONFIGURATION_PER_CHANNEL = False

    DEFAULT_CONFIGURATION = [
        {
            "name": SOCIAL_STRATEGY_CODE,
            "value": 'social_auth.strategy.SaleorPluginStrategy',
        },
        {
            "name": SOCIAL_STORAGE_CODE,
            "value": 'social_django.models.DjangoStorage',
        },
        {
            "name": DEFAULT_BACKEND_CODE,
            "value": '',
        },
        {
            "name": CONFIG_CODE,
            "value": '',
        },
    ]

    CONFIG_STRUCTURE = {
        SOCIAL_STRATEGY_CODE: {
            "type": ConfigurationTypeField.STRING,
            "help_text": 'Should export `.settings`, `.req_data`. `SOCIAL_AUTH_STRATEGY` in `python-social-auth` doc',
            "label": "Social Auth Strategy",
        },
        SOCIAL_STORAGE_CODE: {
            "type": ConfigurationTypeField.STRING,
            "help_text": '`SOCIAL_AUTH_STORAGE` in `python-social-auth` doc',
            "label": "Social Auth Storage",
        },
        DEFAULT_BACKEND_CODE: {
            "type": ConfigurationTypeField.STRING,
            "help_text": 'Default backend when no variable `backend` in graphql request',
            "label": "Default backend name (short form)",
        },
        CONFIG_CODE: {
            "type": ConfigurationTypeField.MULTILINE,
            "help_text": 'In YAML format. Configuration settings refer to `python-social-auth` doc',
            "label": "Configuration",
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
         # self.configuration is an array of dict, just like in the db
        for config in self.configuration:
            config_name = config['name']
            if config_name == CONFIG_CODE:
                self.settings = yaml.safe_load(config['value']) or {}
            else:
                setattr(self, config_name, config['value'])

        logger.info('SocialAuthPlugin.__init__, settings: %s', self.settings)

    def load_strategy(self, request_data: dict, request: WSGIRequest) -> DjangoStrategy:
        strategy_class_str = getattr(self, SOCIAL_STRATEGY_CODE)
        storage_class_str = getattr(self, SOCIAL_STORAGE_CODE)
        strategy = get_strategy(
            strategy_class_str, storage_class_str,
            self.settings, request_data,
            request=request
        )
        if not hasattr(strategy, 'settings') or not hasattr(strategy, 'req_data'):
            raise TypeError(f'`settings` or `req_data` {strategy_class_str} instance are not accessible')
        return strategy

    def load_backend(self, strategy: DjangoStrategy, name: str, redirect_uri: str) -> DjangoStrategy:
        return strategy.get_backend(name, redirect_uri=redirect_uri)

    # @patch_session_to_request
    def external_authentication_url(
        self, data: dict, request: WSGIRequest, previous_value
    ) -> dict:
        storefront_redirect_url = data.get("redirectUri")
        validate_storefront_redirect_url(storefront_redirect_url)

        session = getattr(request, 'session', None)
        # manually create a session as session is not enabled in saleor -- MIDDLEWARE in settings
        if not session:
            session = request.session = SessionStore()
        strategy = self.load_strategy(data, request)

        backend_str = data.get('backend') or getattr(self, DEFAULT_BACKEND_CODE, '')
        backend = self.load_backend(
            strategy,
            backend_str,
            storefront_redirect_url
        )
        if not backend.uses_redirect():
            # for the time being, we only support backend whose`.uses_redirect() == True`
            raise TypeError(f'{backend_str} not support `uses_redirect`')

        # save extra data into session
        do_auth(backend, redirect_name=REDIRECT_FIELD_NAME)
        auth_url = backend.auth_url()

        # save redirect_uri in session for later exchange code request for access token and id token
        strategy.session_set(EXCHANGE_REDIRECT_URI_CODE, storefront_redirect_url)
        # make session_key as state_token for `external_obtain_access_tokens` retrieval
        state_token = backend.get_session_state()
        session._session_key = state_token
        session.save(must_create=True)

        return {"authorizationUrl": auth_url}

    # @patch_session_to_request
    def external_obtain_access_tokens(
        self, data: dict, request: WSGIRequest, previous_value
    ) -> ExternalAccessTokens:
        # data['code'], data['state']
        # token = self.oauth.fetch_access_token()
        state_token = data.get('state')
        if not state_token:
            raise ValidationError('Missing needed parameter `state`')
        session = request.session = SessionStore(session_key=state_token)
        strategy = self.load_strategy(data, request)
        redirect_uri = strategy.session_get(EXCHANGE_REDIRECT_URI_CODE)

        backend_str = data.get('backend') or getattr(self, DEFAULT_BACKEND_CODE, '')
        backend = self.load_backend(
            strategy,
            backend_str,
            redirect_uri
        )
        user = do_complete(backend, _do_login, user=request.user, request=request)

        # copied from
        # saleor/graphql/account/mutations/authentication.py:CreateToken.perform_mutation
        access_token = create_access_token(user)
        csrf_token = _get_new_csrf_token()
        refresh_token = create_refresh_token(user, {"csrfToken": csrf_token})
        request.refresh_token = refresh_token
        request._cached_user = user
        # this will be done via _do_login
        # user.last_login = timezone.now()
        # user.save(update_fields=["last_login"])

        # session is not need any more under spa
        session.delete()
        return ExternalAccessTokens(
            token=access_token, 
            refresh_token=refresh_token, 
            csrf_token=csrf_token,
            user=user,
        )

    def request_data(self, request: WSGIRequest, merge=True):
        # copy from social_django.strategy.DjangoStrategy.request_data
        if not request:
            return {}
        if merge:
            data = request.GET.copy()
            data.update(request.POST)
        elif request.method == 'POST':
            data = request.POST
        else:
            data = request.GET
        return data
