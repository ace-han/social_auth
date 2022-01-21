# social_auth
Social auth plugin (wx, alipay &amp; etc.) for Saleor
> More details will come as the development goes on...

## Plugin Configuration Demo

```yaml
social_strategy: social_auth.strategy.SaleorPluginStrategy

social_storage: social_django.models.DjangoStorage

default_backend: google-openidconnect

social_auth_config: # yaml strings, see below
```

```yaml
# social_auth_config content demo

# https://www.cloudbees.com/blog/yaml-tutorial-everything-you-need-get-started
SOCIAL_AUTH_AUTHENTICATION_BACKENDS:
  - social_core.backends.google_openidconnect.GoogleOpenIdConnect
  - social_auth.backends.weapp.WeappAuth

SOCIAL_AUTH_GOOGLE_OPENIDCONNECT_KEY: xxxyyyzzz.apps.googleusercontent.com
SOCIAL_AUTH_GOOGLE_OPENIDCONNECT_SECRET: YOUR_GOIDC_SECRET

SOCIAL_AUTH_WEIXIN_WEAPP_KEY: wxaaabbbcccdddeee
SOCIAL_AUTH_WEIXIN_WEAPP_SECRET: YOUR_WEAPP_SECRET
```

![image](https://user-images.githubusercontent.com/1177332/150488501-89138aad-191d-43ef-8435-69729736b2ce.png)
