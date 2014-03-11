from __future__ import unicode_literals

import balanced

from django.test import TestCase
from django.contrib.auth.models import User

from django_balanced import models


# https://www.balancedpayments.com/docs/testing
FIXTURES = {
    'card': {
        'card_number': 4111111111111111,
        'expiration_month': 12,
        'expiration_year': 2020,
    },
    'bank_account': {
        'account_number': 123123123,
        'routing_number': 321174851,  # SMCU
        'type': 'savings',
        'name': 'dan carter',
    }
}


class ModelsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.marketplace = balanced.Marketplace().save()

    def setUp(self):
        self.user = User.objects.create_user('john', 'john@test.com', 'pass')
        self.user.save()

        card = balanced.Card(**FIXTURES['card']).save()
        self.card = models.Card.create_from_card_uri(self.user, card.uri)
        self.buyer = self.card.user.balanced_account
        # put some money in the escrow account
        self.buyer.debit(100 * 100, 'test')  # $100.00

    def test_create_credit(self):
        bank_account = models.BankAccount(**FIXTURES['bank_account'])
        bank_account.save()

        # create a second bank account to ensure that we're testing the correct
        # bank account in the case of multiple accounts being available.
        models.BankAccount(**FIXTURES['bank_account']).save()
        credit = bank_account.credit(100)
        self.assertEqual(credit.amount * 100, 100)
        self.assertEqual(credit.bank_account.uri, bank_account.uri)

    def test_create_bank_account(self):
        bank_account = models.BankAccount(**FIXTURES['bank_account'])
        bank_account.save()
        self.assertTrue(bank_account.bank_name)
        self.assertTrue(bank_account.uri)
