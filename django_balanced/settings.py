import os
import logging

from django.conf import settings


LOGGER = logging.getLogger(__name__)

BALANCED = {
    'DASHBOARD_URL': os.environ.get('BALANCED_DASHBOARD_URL',
        'https://dashboard.balancedpayments.com'),
    'API_URL': os.environ.get('BALANCED_API_URL',
        'https://api.balancedpayments.com'),
    'API_KEY': os.environ.get('BALANCED_API_KEY'),
}

BALANCED.update(getattr(settings, 'BALANCED', {}))

if BALANCED['API_KEY'] is None:
    LOGGER.error('You must set the BALANCED_API_KEY environment variable.')

AUTO_CREATE_BALANCED_ACCOUNT = False
