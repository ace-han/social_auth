import logging
from social_core.backends.oauth import BaseOAuth2


logger = logging.getLogger(__name__)

class WeappAuth(BaseOAuth2):
    """
    SOCIAL_AUTH_WEIXIN_WEAPP_KEY = APPID = XXX
    SOCIAL_AUTH_WEIXIN_WEAPP_SECRET = SECRET = XXX
    """
    name = 'weixin-weapp'
    ACCESS_TOKEN_METHOD = 'GET'
    ACCESS_TOKEN_URL = 'https://api.weixin.qq.com/sns/jscode2session'
    # in order to make self.validate_state() = None
    STATE_PARAMETER = False
    REDIRECT_STATE = False

    EXTRA_DATA = [
        # refer to social_core/backends/base.py:BaseAuth.extra_data
        # (name, alias, discard,)
        ('openid', 'openid', False,),
        ('unionid', 'unionid', False,),
        ('session_key', 'session_key', False,),
    ]

    def uses_redirect(self):
        # Not supported. Since it's an app inside auth
        return False

    # @handle_http_errors
    # def auth_complete(self, *args, **kwargs):
    #     api = WXAPPAPI(appid=settings.WX_APP_ID,
    #               app_secret=settings.WX_APP_SECRET)
    #     super().auth_complete()

    # def validate_state(self):
    #     return super().validate_state()

    def auth_complete_params(self, state=None):
        client_id, client_secret = self.get_key_and_secret()
        # refer to
        # https://developers.weixin.qq.com/miniprogram/dev/api-backend/open-api/login/auth.code2Session.html
        return {
            'grant_type': 'authorization_code',
            'js_code': self.data.get('code', ''),
            'appid': client_id,
            'secret': client_secret,
        }

    def request_access_token(self, *args, **kwargs):
        logger.info('weixin-weapp request_access_token start, args: %s, kwargs: %s', args, kwargs)
        resp = super().request_access_token(*args, **kwargs)
        logger.info('weixin-weapp request_access_token end, args: %s, kwargs: %s', args, kwargs)
        # in order to align with `python-social-auth` flow
        # resp = {
        #     "opendid": "",
        #     "session_key": "",
        #     "unionid": "",
        #     "errcode": 0,
        #     "errmsg": "",
        # }
        # ========================
        # the common flow:
        # resp = {
        #     "access_token": ${session_key},
        #     "error": ${errcode},
        #     "error_description": ${errmsg},
        # }
        resp.update({
            "access_token": resp.get('session_key'),
            "error": resp.get('errcode'),
            "error_description": resp.get('errmsg'),
        })
        return resp

    # def auth_headers():
    #     super().auth_headers

    def user_data(self, access_token, *args, **kwargs):
        # use access_token to get user info here
        # construct some user data, like username, email
        # we dont need that here
        response = kwargs.get('response', {})
        return response

    def get_user_details(self, response):
        # super().get_user_details
        unionid_as_username = response.get(self.setting('UNIONID_AS_USERNAME')) or False
        if unionid_as_username:
            username = response.get('unionid')
        else:
            username = response.get('openid')
        email_host = response.get(self.setting('EMAIL_HOST')) or 'qq.com'
        email = f'{username}@{email_host}'
        return {
            "username": username,
            "email": email,
        }

    def get_user_id(self, details, response):
        # in Saleor, we need email as uid
        return details.get('email')


