from django.apps import AppConfig


class DjangoBalancedConfig(AppConfig):
    name = 'django_balanced'

    def ready(self):
        from . import listeners
