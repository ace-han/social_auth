import logging
from typing import Optional
from urllib.parse import urlencode

from django.core.cache import cache
from django.core.exceptions import ValidationError

from social_core.utils import sanitize_redirect

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
