from __future__ import unicode_literals

from django.conf import settings
from django.dispatch import receiver
from django.db.models import signals
from django.contrib.auth import get_user_model

# try:
#     post_sync = signals.post_migrate
# except AttributeError:
#     post_sync = signals.post_syncdb


# This will create an account per user when they are next saved. Subsequent
# saves will not make a network call.
def create_user_profile(sender, instance, created, **kwargs):
    from .models import Account
    Account.objects.get_or_create(user=instance)

if getattr(settings, 'AUTO_CREATE_BALANCED_ACCOUNT', False):
    signals.post_save.connect(create_user_profile, sender=get_user_model())


# We are disabling this because it makes migrations take too long.
# Instead, use the sync management command.

# # Sync with Balanced when the database is synced
# @receiver(post_sync, dispatch_uid='django_balanced.listeners.sync_balanced')
# def sync_balanced(sender, **kwargs):
#     from .models import BankAccount, Credit
#     BankAccount.sync()
#     Credit.sync()
