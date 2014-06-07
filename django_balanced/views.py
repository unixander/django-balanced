from __future__ import unicode_literals

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views import generic

from .formsets import BulkPayoutFormSet
from .models import BankAccount


class AdminBulkPay(generic.TemplateView):
    template_name = 'django_balanced/admin_confirm_bulk_pay.html'

    @method_decorator(staff_member_required)
    def dispatch(self, request, *args, **kwargs):
        if 'bank_account_bulk_pay' not in request.session:
            return redirect('../')
        self.formset = self.get_formset()
        return super(AdminBulkPay, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if '_cancel' in request.POST:
            message = 'Your payouts have been cancelled'
            return self.payout_complete(message)
        if self.formset.is_valid():
            for form in self.formset:
                form.save()
            message = 'Your payouts have been made.'
            return self.payout_complete(message)
        return self.get(request, *args, **kwargs)

    def get_queryset(self):
        bank_account_list = self.request.session['bank_account_bulk_pay']
        queryset = BankAccount.objects.filter(pk__in=bank_account_list)
        queryset = queryset.select_related('user')
        return queryset

    def get_context_data(self, **kwargs):
        context = super(AdminBulkPay, self).get_context_data(**kwargs)
        context['formset'] = self.formset
        return context

    def get_formset(self):
        return BulkPayoutFormSet(self.request.POST or None,
            initial=[{'bank_account': bank_account} for bank_account in
                self.get_queryset()]
        )

    def payout_complete(self, message):
        del self.request.session['bank_account_bulk_pay']
        messages.success(self.request, message)
        return redirect('admin:django_balanced_bankaccount_changelist')
