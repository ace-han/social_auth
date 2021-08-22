from collections import OrderedDict
import logging
from django.apps import apps, AppConfig
from django.conf import settings
from django.core import management

logger = logging.getLogger('saleor')

class SocialAuthConfig(AppConfig):
    name = 'social_auth'
    verbose_name = "Social Auth"

    def ready(self):
        patch_app_names = ('social_django', 'django.contrib.sessions', )
        patch_app_installed = apps.is_installed(patch_app_names[0])

        if patch_app_installed:
            logger.info('SocialAuthConfig.ready, app: %s, is_installed: %s', patch_app_names[0], patch_app_installed)
        else:
            logger.info('SocialAuthConfig.ready, app: %s, is_installed: %s, doing initialization...', patch_app_names[0], patch_app_installed)
            # refer to
            # https://stackoverflow.com/questions/24027901/dynamically-loading-django-apps-at-runtime#answer-57897422
            settings.INSTALLED_APPS += patch_app_names
            apps.app_configs = OrderedDict()
            apps.apps_ready = apps.models_ready = apps.loading = apps.ready = False
            apps.clear_cache()
            apps.populate(settings.INSTALLED_APPS)
            for patch_app_name in patch_app_names:
                management.call_command('migrate', patch_app_name.rsplit('.', maxsplit=1)[-1], interactive=False)
            # management.call_command('migrate', interactive=False)
