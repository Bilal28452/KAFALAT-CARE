import logging
from urllib.parse import urlencode

import requests
from django.conf import settings


logger = logging.getLogger(__name__)


class SafepayError(Exception):
    pass


class SafepayConfigurationError(SafepayError):
    pass


def _configuration():
    environment = settings.SAFEPAY_ENV
    if environment not in {'sandbox', 'production'}:
        raise SafepayConfigurationError('SAFEPAY_ENV must be sandbox or production.')
    if not settings.SAFEPAY_API_KEY or not settings.SAFEPAY_SECRET_KEY:
        raise SafepayConfigurationError('Safepay API credentials are not configured.')

    api_host = (
        'https://api.getsafepay.com'
        if environment == 'production'
        else 'https://sandbox.api.getsafepay.com'
    )
    return environment, api_host


def _post_json(url, payload=None):
    headers = {
        'X-SFPY-MERCHANT-SECRET': settings.SAFEPAY_SECRET_KEY,
        'Content-Type': 'application/json',
    }
    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=settings.SAFEPAY_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as error:
        logger.warning('Safepay API request failed: %s', error.__class__.__name__)
        raise SafepayError('Safepay could not start the checkout. Please try again.') from error
    except ValueError as error:
        raise SafepayError('Safepay returned an invalid response.') from error


def create_checkout_url(payment, success_url, cancel_url):
    environment, api_host = _configuration()
    tracker_token = payment.tracker_token

    if not tracker_token:
        payload = {
            'merchant_api_key': settings.SAFEPAY_API_KEY,
            'intent': 'CYBERSOURCE',
            'mode': 'payment',
            'entry_mode': 'raw',
            'currency': payment.currency,
            'amount': int(payment.amount * 100),
            'metadata': {
                'order_id': str(payment.reference),
            },
            'include_fees': False,
        }
        try:
            result = _post_json(f'{api_host}/order/payments/v3/', payload)
            tracker_token = result['data']['tracker']['token']
        except (KeyError, TypeError) as error:
            raise SafepayError('Safepay returned an invalid payment session.') from error

        if not isinstance(tracker_token, str) or not tracker_token:
            raise SafepayError('Safepay returned an invalid payment tracker.')
        payment.tracker_token = tracker_token
        payment.save(update_fields=['tracker_token', 'updated_at'])

    try:
        result = _post_json(f'{api_host}/client/passport/v1/token')
        auth_token = result['data']
    except (KeyError, TypeError) as error:
        raise SafepayError('Safepay returned an invalid checkout token.') from error

    if not isinstance(auth_token, str) or not auth_token:
        raise SafepayError('Safepay returned an invalid checkout token.')

    checkout_params = urlencode({
        'tbt': auth_token,
        'tracker': tracker_token,
        'environment': environment,
        'source': 'hosted',
        'redirect_url': success_url,
        'cancel_url': cancel_url,
    })
    return f'{api_host}/embedded/?{checkout_params}'
