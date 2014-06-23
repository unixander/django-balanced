import balanced

from django import forms
from django.forms.models import BaseFormSet, formset_factory

from .forms import PayoutForm


class BaseBulkPayoutFormSet(BaseFormSet):
    def clean(self):
        if any(self.errors):
            return
        escrow = balanced.Marketplace.my_marketplace.in_escrow
        total = sum([form.cleaned_data['amount'] for form in self.forms]) * 100
        if total > escrow:
            error = 'You have insufficient funds to cover this payout.'
            raise forms.ValidationError(error)

BulkPayoutFormSet = formset_factory(PayoutForm,
    formset=BaseBulkPayoutFormSet, extra=0)
