import balanced

from decimal import Decimal
from django import forms

from .models import BankAccount, Credit


class BankAccountAddForm(forms.ModelForm):
    name = forms.CharField(max_length=255)
    account_number = forms.CharField(max_length=255)
    routing_number = forms.CharField(max_length=255)
    type = forms.ChoiceField(choices=(
        ('savings', 'savings'), ('checking', 'checking')
    ))

    class Meta:
        fields = ('user',)
        model = BankAccount


class BankAccountChangeForm(forms.ModelForm):
    class Meta:
        fields = ('user',)
        model = BankAccount


class CreditAddForm(forms.ModelForm):
    amount = forms.DecimalField(max_digits=10, decimal_places=2, required=True)
    description = forms.CharField(max_length=255, required=False)
    bank_account = forms.ModelChoiceField(queryset=BankAccount.objects)

    class Meta:
        model = Credit
        exclude = ['status', 'created_at', 'id', 'uri']

    def clean(self):
        if not self.is_valid():
            return self.cleaned_data
        data = self.cleaned_data
        escrow = balanced.Marketplace.my_marketplace.in_escrow
        amount = int(data['amount'] * 100)
        if amount > escrow:
            error = 'You have insufficient funds to cover this transfer.'
            raise forms.ValidationError(error)
        return data


class PayoutForm(forms.Form):
    bank_account = forms.ModelChoiceField(queryset=BankAccount.objects,
        widget=forms.HiddenInput)
    amount = forms.DecimalField(decimal_places=2, min_value=Decimal('.50'))
    description = forms.CharField()

    def save(self):
        assert self.is_valid()
        return self.cleaned_data['bank_account'].credit(
            self.cleaned_data['amount'] * 100,
            self.cleaned_data['description']
        )
