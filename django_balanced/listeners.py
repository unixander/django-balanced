from __future__ import unicode_literals

from django.dispatch import receiver
from django.db.models import signals

try:
    from django.contrib.auth import get_user_model
except ImportError:
    from django.contrib.auth.models import User
    get_user_model = lambda: User

try:
    post_sync = signals.post_migrate
except AttributeError:
    post_sync = signals.post_syncdb


# This will create an account per user when they are next saved. Subsequent
# saves will not make a network call.
@receiver(signals.post_save, sender=get_user_model())
def create_user_profile(sender, instance, created, **kwargs):
    from .models import Account
    Account.objects.get_or_create(user=instance)


# Sync with Balanced when the database is synced
@receiver(post_sync, dispatch_uid='django_balanced.listeners.sync_balanced')
def sync_balanced(sender, **kwargs):
    from .models import BankAccount, Credit
    BankAccount.sync()
    Credit.sync()
