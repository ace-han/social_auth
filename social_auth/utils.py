import logging
from typing import Optional
from urllib.parse import urlencode

from django.core.cache import cache
from django.core.exceptions import ValidationError

from social_core.utils import partial_pipeline_data, sanitize_redirect, user_is_active, user_is_authenticated

from saleor.core.utils import build_absolute_uri
from saleor.core.utils.url import prepare_url, validate_storefront_url
from saleor.plugins.error_codes import PluginErrorCode

logger = logging.getLogger(__name__)


def validate_storefront_redirect_url(storefront_redirect_uri: Optional[str]):
    if not storefront_redirect_uri:
        raise ValidationError(
            {
                "redirectUri": ValidationError(
                    "Missing redirect uri.", code=PluginErrorCode.NOT_FOUND.value
                )
            }
        )
    try:
        validate_storefront_url(storefront_redirect_uri)
    except ValidationError as error:
        raise ValidationError(
            {"redirectUrl": error}, code=PluginErrorCode.INVALID.value
        )


def prepare_redirect_url(
    plugin_id, storefront_redirect_url: Optional[str] = None
) -> str:
    """Prepare redirect url used by auth service to return to Saleor.

    /plugins/mirumee.authentication.openidconnect/callback?redirectUrl=https://localhost:3000/
    """
    params = {}
    if storefront_redirect_url:
        params["redirectUrl"] = storefront_redirect_url
    redirect_url = build_absolute_uri(f"/plugins/{plugin_id}/callback")

    return prepare_url(urlencode(params), redirect_url)  # type: ignore


def do_auth(backend, redirect_name='next'):
    # ======no need, since it's an spa application=====
    # copy from `social_core.actions:do_auth`
    # Save any defined next value into session
    data = backend.strategy.request_data(merge=False)

    # Save extra data into session.
    for field_name in backend.setting('FIELDS_STORED_IN_SESSION', []):
        if field_name in data:
            backend.strategy.session_set(field_name, data[field_name])
        else:
            backend.strategy.session_set(field_name, None)

    if redirect_name in data:
        # Check and sanitize a user-defined GET/POST next field value
        redirect_uri = data[redirect_name]
        if backend.setting('SANITIZE_REDIRECTS', True):
            allowed_hosts = backend.setting('ALLOWED_REDIRECT_HOSTS', []) + \
                            [backend.strategy.request_host()]
            redirect_uri = sanitize_redirect(allowed_hosts, redirect_uri)
        backend.strategy.session_set(
            redirect_name,
            redirect_uri or backend.setting('LOGIN_REDIRECT_URL')
        )


def do_complete(backend, login, user=None,
                *args, **kwargs):
    is_authenticated = user_is_authenticated(user)
    user = user if is_authenticated else None

    partial = partial_pipeline_data(backend, user, *args, **kwargs)
    if partial:
        user = backend.continue_pipeline(partial)
        # clean partial data after usage
        backend.strategy.clean_partial_pipeline(partial.token)
    else:
        user = backend.complete(user=user, *args, **kwargs)

    # check if the output value is something else than a user and just
    # return it to the client
    user_model = backend.strategy.storage.user.user_model()
    if user and not isinstance(user, user_model):
        # raise an error here in our graphql situation
        return user

    if user:
        if user_is_active(user):
            # catch is_new/social_user in case login() resets the instance
            social_user = user.social_user
            login(backend, user, social_user)
            # store last login backend name in session
            backend.strategy.session_set('social_auth_last_login_backend',
                                         social_user.provider)

        else:
            if backend.setting('INACTIVE_USER_LOGIN', False):
                social_user = user.social_user
                login(backend, user, social_user)
    return user

