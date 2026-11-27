import hashlib
import hmac
import json
import logging
from decimal import Decimal, InvalidOperation
from uuid import UUID

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from accounts.models import AccountProfile
from donations.models import Donation
from sponsorships.models import Sponsorship

from .gateway import SafepayConfigurationError, SafepayError, create_checkout_url
from .models import Payment, PaymentWebhookEvent
from .services import get_or_create_donation_payment, get_or_create_sponsorship_payment


logger = logging.getLogger(__name__)


def checkout_redirect(request, payment, fallback_url):
    success_url = f'{settings.SITE_URL}{reverse("payment_return")}?reference={payment.reference}'
    cancel_url = f'{settings.SITE_URL}{reverse("payment_cancel")}?reference={payment.reference}'
    try:
        checkout_url = create_checkout_url(payment, success_url, cancel_url)
    except (SafepayConfigurationError, SafepayError):
        logger.exception('Could not create Safepay checkout for payment %s.', payment.reference)
        messages.error(
            request,
            'Secure checkout is temporarily unavailable. Check the payment configuration and try again.',
        )
        return redirect(fallback_url)
    return redirect(checkout_url)


@login_required(login_url='donor_login')
@require_POST
def donation_checkout(request, donation_id):
    profile = getattr(request.user, 'account_profile', None)
    if not profile or profile.role != AccountProfile.ROLE_DONOR:
        return HttpResponse('Only donors can pay online donations.', status=403)
    donation = get_object_or_404(Donation, pk=donation_id, donor=request.user)
    try:
        payment = get_or_create_donation_payment(donation)
    except ValueError as error:
        messages.info(request, str(error))
        return redirect('donor_donation_detail', pk=donation.pk)
    return checkout_redirect(
        request,
        payment,
        reverse('donor_donation_detail', kwargs={'pk': donation.pk}),
    )


@login_required(login_url='sponsor_login')
@require_POST
def sponsorship_checkout(request, sponsorship_id):
    profile = getattr(request.user, 'account_profile', None)
    if not profile or profile.role != AccountProfile.ROLE_SPONSOR:
        return HttpResponse('Only sponsors can pay sponsorships.', status=403)
    sponsorship = get_object_or_404(
        Sponsorship,
        pk=sponsorship_id,
        sponsor=request.user,
    )
    try:
        payment = get_or_create_sponsorship_payment(sponsorship)
    except ValueError as error:
        messages.error(request, str(error))
        return redirect('sponsor_dashboard')
    fallback_url = (
        reverse('sponsor_child_detail', kwargs={'pk': sponsorship.child_id})
        if sponsorship.child_id
        else reverse('sponsor_dashboard')
    )
    return checkout_redirect(request, payment, fallback_url)


def _payment_for_return(request):
    reference = request.GET.get('reference', '').strip()
    if reference:
        try:
            payment_reference = UUID(reference)
        except (TypeError, ValueError, AttributeError):
            payment_reference = None
        if payment_reference:
            payment = Payment.objects.filter(
                reference=payment_reference,
                initiated_by=request.user,
            ).select_related('donation', 'sponsorship').first()
            if payment is not None:
                return payment

    tracker_token = request.GET.get('tracker', '').strip()
    if not tracker_token:
        return None
    return Payment.objects.filter(
        tracker_token=tracker_token,
        initiated_by=request.user,
    ).select_related('donation', 'sponsorship').first()


def _payment_destination(payment, user):
    profile = getattr(user, 'account_profile', None)

    if payment.sponsorship_id:
        sponsorship = payment.sponsorship
        if profile and profile.role == AccountProfile.ROLE_SPONSOR:
            if (
                sponsorship.sponsor_id == user.pk
                and sponsorship.status == 'active'
                and sponsorship.child_id
            ):
                return reverse('sponsor_child_detail', kwargs={'pk': sponsorship.child_id})
            return f'{reverse("sponsor_dashboard")}?section=payments'

    if payment.donation_id and profile and profile.role == AccountProfile.ROLE_DONOR:
        return reverse('donor_donation_detail', kwargs={'pk': payment.donation_id})

    return reverse('index')


@login_required(login_url='login')
def payment_return(request):
    payment = _payment_for_return(request)
    if payment is None:
        return render(request, 'payments/payment_result.html', {
            'payment': None,
            'payment_returned': True,
        }, status=404)
    if payment.status == Payment.STATUS_PAID:
        return redirect(_payment_destination(payment, request.user))
    return render(request, 'payments/payment_result.html', {
        'payment': payment,
        'payment_returned': True,
        'status_url': f'{reverse("payment_status")}?reference={payment.reference}',
    })


@login_required(login_url='login')
def payment_cancel(request):
    payment = _payment_for_return(request)
    if payment is None:
        return render(request, 'payments/payment_result.html', {
            'payment': None,
            'payment_returned': False,
        }, status=404)
    if payment.status == Payment.STATUS_PAID:
        return redirect(_payment_destination(payment, request.user))
    return render(request, 'payments/payment_result.html', {
        'payment': payment,
        'payment_returned': False,
    })


@login_required(login_url='login')
@require_GET
@never_cache
def payment_status(request):
    """Return the current server-verified status for the signed-in payer."""
    payment = _payment_for_return(request)
    if payment is None:
        return JsonResponse({'error': 'Payment not found.'}, status=404)

    response = {'status': payment.status}
    if payment.status == Payment.STATUS_PAID:
        response['redirect_url'] = _payment_destination(payment, request.user)
    return JsonResponse(response)


def _valid_webhook_signature(raw_body, signature):
    secret = settings.SAFEPAY_WEBHOOK_SECRET
    if not secret or not signature:
        return False
    expected = hmac.new(
        secret.encode('utf-8'),
        raw_body,
        hashlib.sha512,
    ).hexdigest()
    return hmac.compare_digest(expected, signature.strip())


def _mark_payment_paid(payment):
    payment.status = Payment.STATUS_PAID
    payment.paid_at = timezone.now()
    payment.save(update_fields=['status', 'paid_at', 'updated_at'])

    if payment.donation_id:
        donation = Donation.objects.select_for_update().get(pk=payment.donation_id)
        donation.status = 'completed'
        donation.payment_method = 'Safepay'
        donation.transaction_id = payment.tracker_token or ''
        donation.donated_at = timezone.localdate()
        donation.save(update_fields=[
            'status',
            'payment_method',
            'transaction_id',
            'donated_at',
        ])
    else:
        sponsorship = Sponsorship.objects.select_for_update().get(pk=payment.sponsorship_id)
        sponsorship.last_payment_date = timezone.localdate()
        sponsorship.payment_method = 'Safepay'
        update_fields = ['last_payment_date', 'payment_method']
        if sponsorship.status == 'active':
            from accounts.views.sponsor_views import add_calendar_month

            sponsorship.next_payment_date = add_calendar_month(timezone.localdate())
            update_fields.append('next_payment_date')
        sponsorship.save(update_fields=update_fields)


def _apply_webhook_event(event_type, event_data):
    tracker_token = event_data.get('tracker')
    if not isinstance(tracker_token, str) or not tracker_token:
        raise ValueError('Webhook tracker is missing.')

    payment = Payment.objects.select_for_update().filter(tracker_token=tracker_token).first()
    if payment is None:
        raise LookupError('No local payment matches the webhook tracker.')

    if event_type == 'payment.succeeded':
        try:
            received_amount = Decimal(str(event_data['amount']))
        except (KeyError, InvalidOperation, TypeError, ValueError) as error:
            raise ValueError('Webhook payment amount is invalid.') from error
        expected_amount = payment.amount * 100
        if (
            received_amount != expected_amount
            or event_data.get('currency') != payment.currency
            or event_data.get('state') != 'TRACKER_ENDED'
        ):
            raise ValueError('Webhook payment details do not match the stored payment.')
        if payment.status != Payment.STATUS_PAID:
            _mark_payment_paid(payment)
    elif event_type == 'payment.failed' and payment.status != Payment.STATUS_PAID:
        payment.status = Payment.STATUS_FAILED
        payment.save(update_fields=['status', 'updated_at'])
        if payment.donation_id and not Payment.objects.filter(
            donation_id=payment.donation_id,
            status=Payment.STATUS_PAID,
        ).exists():
            Donation.objects.filter(pk=payment.donation_id).update(status='failed')


@csrf_exempt
@require_POST
def safepay_webhook(request):
    signature = request.headers.get('X-SFPY-SIGNATURE', '')
    if not _valid_webhook_signature(request.body, signature):
        return HttpResponse('Invalid webhook signature.', status=400)

    try:
        payload = json.loads(request.body)
        event_token = payload['token']
        event_type = payload['type']
        event_data = payload.get('data', {})
        if not isinstance(event_token, str) or not isinstance(event_type, str):
            raise ValueError('Webhook event identity is invalid.')
        if not isinstance(event_data, dict):
            raise ValueError('Webhook data is invalid.')
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return HttpResponseBadRequest('Invalid webhook payload.')

    with transaction.atomic():
        webhook_event, created = PaymentWebhookEvent.objects.get_or_create(
            event_token=event_token,
            defaults={'event_type': event_type},
        )
        if not created:
            return HttpResponse('Webhook already received.', status=200)

        if event_type in {'payment.succeeded', 'payment.failed'}:
            try:
                _apply_webhook_event(event_type, event_data)
            except LookupError:
                webhook_event.delete()
                logger.warning('Safepay webhook references an unknown tracker.')
                return HttpResponse('Payment tracker not found.', status=404)
            except ValueError:
                webhook_event.delete()
                logger.warning('Safepay webhook has invalid payment details.')
                return HttpResponseBadRequest('Invalid payment event.')

        webhook_event.processed = True
        webhook_event.save(update_fields=['processed'])

    return HttpResponse('Webhook received.', status=200)
