from django.shortcuts import resolve_url
from django.utils.encoding import force_text
from django.utils.functional import Promise
from social_django.strategy import DjangoStrategy

class SaleorPluginStrategy(DjangoStrategy):

    def __init__(self, storage, settings, request_data, *args, **kwargs):
        # loading settings from dashboard admin
        self.settings = settings
        self.req_data = request_data
        super().__init__(storage, *args, **kwargs)

    def get_setting(self, name):
        # copy from social_django.strategy.DjangoStrategy
        value = self.settings[name]
        # Force text on URL named settings that are instance of Promise
        if name.endswith('_URL'):
            if isinstance(value, Promise):
                value = force_text(value)
            value = resolve_url(value)
        return value

    def request_data(self, merge=True):
        # graphql may not include query_string or data in request directly
        return self.req_data

    def authenticate(self, backend, *args, **kwargs):
        kwargs['strategy'] = self
        kwargs['storage'] = self.storage
        kwargs['backend'] = backend
        # we need to assign request as `args` first element according to debug
        args = args + (kwargs.pop('request'), )
        return backend.authenticate(*args, **kwargs)