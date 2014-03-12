from __future__ import unicode_literals

from django.conf.urls import patterns, url
from django.contrib import admin
from django.shortcuts import redirect

from . import views
from .forms import BankAccountAddForm, BankAccountChangeForm, CreditAddForm
from .models import BankAccount, Credit

"""
TODO:
    Add account URI onto django users
"""


class BalancedAdmin(admin.ModelAdmin):
    add_form = None

    def get_form(self, request, obj=None, **kwargs):
        defaults = {}
        if obj is None and self.add_form:
            defaults.update({
                'form': self.add_form,
            })
        defaults.update(kwargs)
        return super(BalancedAdmin, self).get_form(request, obj, **defaults)


class BankAccountAdmin(BalancedAdmin):
    actions = ('bulk_pay_action',)
    list_display = ('account_number', 'created_at', 'user', 'name',
                    'bank_name', 'type', 'dashboard_link')
    list_filter = ('type', 'bank_name', 'user')
    add_form = BankAccountAddForm
    form = BankAccountChangeForm
    raw_id_fields = ('user',)
    search_fields = ('name', 'account_number')

    def bulk_pay_action(self, request, queryset):
        request.session['bank_account_bulk_pay'] = [bank_account.pk for
            bank_account in queryset]
        return redirect('admin:bank_account_bulk_pay')
    bulk_pay_action.short_description = 'Credit selected accounts'

    def get_urls(self):
        urlpatterns = patterns('django_balanced.admin',
            url(r'^bulk_pay/$', views.AdminBulkPay.as_view(),
                name='bank_account_bulk_pay')
        ) + super(BankAccountAdmin, self).get_urls()
        return urlpatterns

    def save_model(self, request, obj, form, change):
        if isinstance(form, self.add_form):
            data = form.cleaned_data
            obj.name = data['name']
            obj.account_number = data['account_number']
            obj.routing_number = data['routing_number']
            obj.type = data['type']
            if data['user']:
                obj.user = data['user']
        super(BankAccountAdmin, self).save_model(request, obj, form, change)

admin.site.register(BankAccount, BankAccountAdmin)


class CreditAdmin(BalancedAdmin):
    add_form = CreditAddForm
    list_display = ('user', 'bank_account', 'amount', 'description',
        'status', 'dashboard_link')
    list_filter = ('user', 'status')
    search_fields = ('amount', 'description', 'status')

    def save_model(self, request, obj, form, change):
        if isinstance(form, self.add_form):
            data = form.cleaned_data
            obj.amount = int(data['amount'] * 100)
            obj.bank_account = data['bank_account']
            obj.user = data['bank_account'].user
            obj.description = data['description']
        return super(CreditAdmin, self).save_model(request, obj, form, change)

admin.site.register(Credit, CreditAdmin)
