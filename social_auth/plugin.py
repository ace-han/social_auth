import logging

from saleor.plugins.base_plugin import BasePlugin, ConfigurationTypeField

logger = logging.getLogger(__name__)

class SocialAuthPlugin(BasePlugin):
    PLUGIN_ID = 'tinaam.authentication.SocialAuthPlugin'
    PLUGIN_NAME = "Social Auth"
    CONFIGURATION_PER_CHANNEL = True

    DEFAULT_CONFIGURATION = [
        {
            "name": 'weapp_appid',
            "value": '',
        },
    ]

    CONFIG_STRUCTURE = {
        'weapp_appid': {
            "type": ConfigurationTypeField.STRING,
            "help_text": 'weapp app_id',
            "label": "weapp app_id",
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Convert to dict to easier take config elements
        configuration = {
            item["name"]: item["value"]
            for item in self.configuration
        }
        logger.info('SocialAuthPlugin.__init__, config: %s', configuration)


