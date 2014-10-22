from __future__ import unicode_literals
from datetime import datetime

import balanced

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models

from .settings import BALANCED

try:
    from django import apps
except ImportError:
    # We're in Django <1.7 and can't rely on the apps registry.
    # Fall back to importing listeners here.
    from . import listeners

if BALANCED.get('API_KEY'):
    balanced.configure(BALANCED['API_KEY'])

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


class BalancedException(Exception):
    pass


class BalancedResource(models.Model):
    _resource = balanced.Resource
    id = models.CharField(max_length=255, editable=False)
    uri = models.CharField(primary_key=True, max_length=255, editable=False)
    created_at = models.DateTimeField(auto_created=True, editable=False)

    class Meta:
        abstract = True

    def dashboard_link(self):
        return '<a href="%s%s" target="_blank">View on Balanced</a>' % (
            BALANCED['DASHBOARD_URL'],
            self.uri[3:]
        )
    dashboard_link.allow_tags = True

    def find(self):
        return self._resource.find(self.uri)

    @classmethod
    def sync(cls):
        for resource in cls._resource.query:
            try:
                existing = cls.objects.get(uri=resource.uri)
            except cls.DoesNotExist:
                existing = cls()
            existing._sync(resource)
            existing.save()

    def _sync(self, obj):
        for field in self._meta.get_all_field_names():
            has = hasattr(obj, field)
            value = has and getattr(obj, field)
            if has and isinstance(value, (basestring, int, datetime)):
                setattr(self, field, value)


class BankAccount(BalancedResource):
    _resource = balanced.BankAccount

    user = models.ForeignKey(AUTH_USER_MODEL,
                             related_name='bank_accounts',
                             null=True)
    account_number = models.CharField(editable=False, max_length=255)
    name = models.CharField(editable=False, max_length=255)
    routing_number = models.CharField(editable=False, max_length=255)
    bank_name = models.CharField(editable=False, max_length=255)
    type = models.CharField(editable=False, max_length=255)

    class Meta:
        # app_label = 'Balanced'
        db_table = 'balanced_bank_accounts'

    def __str__(self):
        return '{} {} {}'.format(self.user, self.bank_name, self.account_number)

    def save(self, **kw):
        if not self.uri:
            bank_account = self._resource(
                routing_number=self.routing_number,
                account_number=self.account_number,
                name=self.name,
                type=self.type,
            )
        else:
            bank_account = self.find()
        try:
            bank_account.save()
        except balanced.exc.HTTPError as ex:
            raise ex

        self._sync(bank_account)
        super(BankAccount, self).save(**kw)

    def delete(self, using=None):
        bank_account = self.find()
        bank_account.delete()
        super(BankAccount, self).delete(using)

    def credit(self, amount, description=None, meta=None, statement_descriptor=None):
        bank_account = self.find()
        credit = bank_account.credit(amount, description, meta, statement_descriptor)

        django_credit = Credit()
        django_credit._sync(credit)
        django_credit.bank_account = self
        django_credit.user = self.user
        django_credit.amount /= 100.0
        django_credit.statement_descriptor = statement_descriptor
        django_credit.save()

        return django_credit

    def debit(self, amount, description, statement_descriptor=None):
        account = self.user.balanced_account
        return account.debit(
            amount=amount,
            description=description,
            appears_on_statement_as=statement_descriptor,
            bank_account=self,
        )


class Card(BalancedResource):
    _resource = balanced.Card

    user = models.ForeignKey(AUTH_USER_MODEL,
                             related_name='cards',
                             null=False)
    name = models.CharField(editable=False, max_length=255)
    expiration_month = models.IntegerField(editable=False)
    expiration_year = models.IntegerField(editable=False)
    last_four = models.CharField(editable=False, max_length=4)
    brand = models.CharField(editable=False, max_length=255)

    class Meta:
        # app_label = 'Balanced'
        db_table = 'balanced_cards'

    def __str__(self):
        return '{} {} {}'.format(self.user, self.brand, self.last_four)

    @classmethod
    def create_from_card_uri(cls, user, card_uri):
        card = cls(user=user)
        card.save(card_uri)
        return card

    def save(self, card_uri=None, **kwargs):
        # a card must be saved elsewhere since we don't store the data required
        # to create a card from the django object
        if not self.uri:
            account = self.user.balanced_account.find()
            account.add_card(card_uri=card_uri)
            self.uri = card_uri
        card = self.find()
        self._sync(card)

        super(Card, self).save(**kwargs)

    def delete(self, using=None):
        card = self.find()
        card.is_valid = False
        card.save()
        super(Card, self).delete(using)

    def debit(self, amount, description, statement_descriptor=None):
        account = self.user.balanced_account
        return account.debit(
            amount=amount,
            description=description,
            appears_on_statement_as=statement_descriptor,
            card=self,
        )


class Credit(BalancedResource):
    _resource = balanced.Credit

    user = models.ForeignKey(AUTH_USER_MODEL,
                             related_name='credits',
                             editable=False,
                             null=True)
    bank_account = models.ForeignKey(BankAccount,
                                     related_name='credits',
                                     editable=False)
    amount = models.DecimalField(editable=False,
                                 decimal_places=2,
                                 max_digits=10)
    description = models.CharField(max_length=255, null=True)
    statement_descriptor = models.CharField(max_length=12, null=True)
    status = models.CharField(editable=False, max_length=255)

    class Meta:
        # app_label = 'Balanced'
        db_table = 'balanced_credits'

    def save(self, **kwargs):
        if not self.uri:
            bank_account = self.bank_account.find()
            credit = self._resource(
                uri=bank_account.credits_uri,
                amount=self.amount,
                description=self.description,
                appears_on_statement_as=self.statement_descriptor,
            )
            try:
                credit.save()
            except balanced.exc.HTTPError as ex:
                raise ex
        else:
            credit = self.find()

        self._sync(credit)
        self.amount = credit.amount / 100.0
        if not self.bank_account_id:
            bank_account = BankAccount.objects.get(pk=credit.bank_account.uri)
            self.bank_account = bank_account

        super(Credit, self).save(**kwargs)

    def delete(self, using=None):
        raise NotImplemented


class Debit(BalancedResource):
    _resource = balanced.Debit

    user = models.ForeignKey(AUTH_USER_MODEL,
                             related_name='debits',
                             null=False)
    amount = models.DecimalField(editable=False,
                                 decimal_places=2,
                                 max_digits=10)
    description = models.CharField(editable=False, max_length=255)
    statement_descriptor = models.CharField(max_length=12, null=True)
    card = models.ForeignKey(Card,
                             related_name='debits',
                             editable=False,
                             blank=True,
                             null=True)
    bank_account = models.ForeignKey(BankAccount,
                                     related_name='debits',
                                     editable=False,
                                     blank=True,
                                     null=True)

    class Meta:
        # app_label = 'Balanced'
        db_table = 'balanced_debits'

    def clean(self):
        if not self.card or self.bank_account:
            raise ValidationError(
                _('Must have either "card" or "bank_account"'),
                code='invalid',)
        if self.card and self.bank_account:
            raise ValidationError(
                _('Cannot include both "card" and "bank_account"'),
                code='invalid',)
        return super(Debit, self).clean()

    def save(self, **kwargs):
        if not self.uri:
            account = self.user.balanced_account.find()
            if self.card:
                source_uri = self.card.uri
            elif self.bank_account:
                source_uri = self.bank_account.uri
            else:
                source_uri = self.user.cards.all()[0].uri
            debit = account.debit(
                amount=self.amount,
                description=self.description,
                appears_on_statement_as=self.statement_descriptor,
                source_uri=source_uri,
            )
            try:
                debit.save()
            except balanced.exc.HTTPError as ex:
                raise ex
        else:
            debit = self.find()

        self._sync(debit)
        super(Debit, self).save(**kwargs)

    def refund(self, amount, description, meta={}):
        debit = self._resource.find(self.uri)
        return debit.refund(
            amount=amount,
            description=description,
            meta=meta
        )

    def delete(self, using=None):
        raise NotImplemented


class Account(BalancedResource):
    _resource = balanced.Account

    user = models.OneToOneField(AUTH_USER_MODEL,
        related_name='balanced_account')

    class Meta:
        db_table = 'balanced_accounts'

    def save(self, **kwargs):
        if not self.uri:
            ac = balanced.Account(
                name=self.user.username,
            )
            try:
                ac.save()
            except balanced.exc.HTTPError as ex:
                raise ex
            self._sync(ac)

        super(Account, self).save(**kwargs)

    def debit(self, amount, description, card=None, bank_account=None, statement_descriptor=None):
        debit = Debit(
            amount=amount,
            description=description,
            statement_descriptor=statement_descriptor,
            user=self.user,
        )
        if card:
            debit.card = card
        elif bank_account:
            debit.bank_account = bank_account
        debit.save()
        return debit

    def credit(self, amount, description, bank_account, statement_descriptor=None):
        credit = Credit(
            amount=amount,
            description=description,
            statement_descriptor=statement_descriptor,
            user=self.user,
            bank_account=bank_account,
            status='s' # scheduled
        )
        credit.save()
        return credit

    def delete(self, using=None):
        raise NotImplemented
