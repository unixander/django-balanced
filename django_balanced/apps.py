from django.apps import AppConfig


class DjangoBalancedConfig(AppConfig):
    name = 'django_balanced'

    def ready(self):
        print 'HELLO'
        from . import listeners
