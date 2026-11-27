from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db.models import Count, Q
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import AccountProfile
from payments.models import Payment
from payments.services import has_verified_sponsorship_payment
from accounts.views import is_admin_user, resolve_redirect
from accounts.dashboard import record_audit_log
from staff_management.access import is_caretaker
from staff_management.models import StaffMember
from .forms import SponsorMessageForm, SponsorshipForm
from .models import Notification, Sponsorship, SponsorshipConversation, SponsorshipMessage
from .notifications import notify_users
from children.models import Child


# ==================== SPONSORSHIP CRUD VIEWS ====================

@login_required(login_url='admin_login')
def sponsorship_list(request):
    """List all sponsorships with search and filter"""
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')

    sponsorships = Sponsorship.objects.select_related('child').all()

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        sponsorships = sponsorships.filter(
            Q(sponsor_code__icontains=search_query) |
            Q(sponsor_name__icontains=search_query) |
            Q(cnic__icontains=search_query) |
            Q(child__full_name__icontains=search_query)
        )

    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        sponsorships = sponsorships.filter(status=status_filter)

    record_audit_log(request, 'VIEW', 'Sponsorships', details='Viewed sponsorships list')

    context = {
        'sponsorships': sponsorships,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    return render(request, 'sponsorships/sponsorship_list.html', context)


@login_required(login_url='admin_login')
def sponsorship_create(request):
    """Create a new sponsorship record"""
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')

    if request.method == 'POST':
        form = SponsorshipForm(request.POST)
        if form.is_valid():
            sponsorship = form.save(commit=False)
            sponsorship.save()

            # Update child's sponsor status
            if sponsorship.child:
                sponsorship.child.sponsor_status = 'sponsored'
                sponsorship.child.save()

            record_audit_log(
                request, 'CREATE', 'Sponsorships',
                record_id=sponsorship.sponsor_code,
                details=f'Created sponsorship: {sponsorship.sponsor_name} -> {sponsorship.child}'
            )
            messages.success(request, f'Sponsorship for {sponsorship.sponsor_name} created successfully.')
            return redirect(resolve_redirect(request, reverse('sponsorship_detail', kwargs={'pk': sponsorship.pk})))
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SponsorshipForm()

    context = {'form': form, 'action': 'Create'}
    return render(request, 'sponsorships/sponsorship_form.html', context)


@login_required(login_url='admin_login')
def sponsorship_detail(request, pk):
    """View detailed sponsorship information"""
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')

    sponsorship = get_object_or_404(Sponsorship.objects.select_related('child'), pk=pk)

    record_audit_log(
        request, 'VIEW', 'Sponsorships',
        record_id=sponsorship.sponsor_code,
        details=f'Viewed sponsorship details: {sponsorship.sponsor_name}'
    )

    context = {
        'sponsorship': sponsorship,
        'payment_transactions': sponsorship.payment_transactions.all(),
    }
    return render(request, 'sponsorships/sponsorship_detail.html', context)


@login_required(login_url='admin_login')
def sponsorship_update(request, pk):
    """Update an existing sponsorship record"""
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')

    sponsorship = get_object_or_404(Sponsorship, pk=pk)
    old_child = sponsorship.child
    old_status = sponsorship.status

    if request.method == 'POST':
        form = SponsorshipForm(request.POST, instance=sponsorship)
        if form.is_valid():
            with transaction.atomic():
                sponsorship = form.save()

                if old_child != sponsorship.child:
                    if old_child and not Sponsorship.objects.filter(
                        child=old_child,
                        status__in=['active', 'paused'],
                    ).exclude(pk=sponsorship.pk).exists():
                        Child.objects.filter(pk=old_child.pk).update(sponsor_status='available')
                    if sponsorship.child:
                        Child.objects.filter(pk=sponsorship.child_id).update(sponsor_status='sponsored')
                elif (
                    old_status in ['active', 'paused']
                    and sponsorship.status not in ['active', 'paused']
                    and sponsorship.child
                    and not Sponsorship.objects.filter(
                        child_id=sponsorship.child_id,
                        status__in=['active', 'paused'],
                    ).exclude(pk=sponsorship.pk).exists()
                ):
                    Child.objects.filter(pk=sponsorship.child_id).update(sponsor_status='available')
                elif (
                    old_status not in ['active', 'paused']
                    and sponsorship.status in ['active', 'paused']
                    and sponsorship.child
                ):
                    Child.objects.filter(pk=sponsorship.child_id).update(sponsor_status='sponsored')

            record_audit_log(
                request, 'UPDATE', 'Sponsorships',
                record_id=sponsorship.sponsor_code,
                details=f'Updated sponsorship: {sponsorship.sponsor_name}'
            )
            messages.success(request, f'Sponsorship for {sponsorship.sponsor_name} updated successfully.')
            return redirect(resolve_redirect(request, reverse('sponsorship_detail', kwargs={'pk': sponsorship.pk})))
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SponsorshipForm(instance=sponsorship)

    context = {'form': form, 'action': 'Update', 'sponsorship': sponsorship}
    return render(request, 'sponsorships/sponsorship_form.html', context)


@login_required(login_url='admin_login')
def sponsorship_delete(request, pk):
    """Delete a sponsorship record"""
    if not is_admin_user(request.user):
        messages.error(request, 'Access denied.')
        return redirect('index')

    sponsorship = get_object_or_404(Sponsorship, pk=pk)

    if request.method == 'POST':
        sponsor_name = sponsorship.sponsor_name
        sponsor_code = sponsorship.sponsor_code
        child_id = sponsorship.child_id
        try:
            with transaction.atomic():
                sponsorship.delete()
                if child_id and not Sponsorship.objects.filter(
                    child_id=child_id,
                    status__in=['active', 'paused'],
                ).exists():
                    Child.objects.filter(pk=child_id).update(sponsor_status='available')
        except ProtectedError:
            messages.error(
                request,
                'This sponsorship cannot be deleted because it has payment records. '
                'End the sponsorship instead to preserve its payment history.',
            )
            return redirect('sponsorship_detail', pk=sponsorship.pk)

        record_audit_log(
            request, 'DELETE', 'Sponsorships',
            record_id=sponsor_code,
            details=f'Deleted sponsorship: {sponsor_name}'
        )
        messages.success(request, f'Sponsorship for {sponsor_name} deleted successfully.')
        return redirect(resolve_redirect(request, reverse('sponsorship_list')))

    payment_count = sponsorship.payment_transactions.count()
    context = {
        'sponsorship': sponsorship,
        'payment_count': payment_count,
        'has_payment_history': payment_count > 0,
    }
    return render(request, 'sponsorships/sponsorship_confirm_delete.html', context)


def calculate_sponsorship_match(child):
    score = 50
    if child.health_status in ('under_care', 'medical_care', 'observation'):
        score += 18
    elif child.health_status == 'healthy':
        score += 10
    if hasattr(child, 'education_record'):
        score += 12
    if getattr(child, 'education_level', ''):
        score += 8
    if child.photo:
        score += 4
    if child.date_of_birth:
        score += 4
    return min(score, 98)


@login_required(login_url='admin_login')
def sponsorship_approve(request, pk):
    if not is_admin_user(request.user):
        return redirect('index')
    sponsorship = get_object_or_404(Sponsorship, pk=pk)
    if request.method == 'POST' and sponsorship.status == 'pending':
        if sponsorship.sponsor_id and Sponsorship.objects.filter(
            sponsor_id=sponsorship.sponsor_id,
            status__in=['pending', 'active', 'paused'],
        ).exclude(pk=sponsorship.pk).exists():
            messages.error(request, 'This sponsor account already has a pending or current sponsorship.')
            return redirect('sponsorship_detail', pk=sponsorship.pk)

        available = Child.objects.filter(sponsor_status='available')
        ranked = sorted(available, key=lambda child: calculate_sponsorship_match(child), reverse=True)
        if not ranked:
            messages.error(request, 'No available child is available for matching.')
            return redirect('sponsorship_detail', pk=sponsorship.pk)
        child = ranked[0]
        try:
            with transaction.atomic():
                sponsorship.child = child
                sponsorship.status = 'active'
                sponsorship.ai_match_score = calculate_sponsorship_match(child)
                sponsorship.admin_notes = request.POST.get('admin_notes', '').strip()
                sponsorship.save()
                child.sponsor_status = 'sponsored'
                child.save(update_fields=['sponsor_status'])
        except IntegrityError:
            messages.error(request, 'This sponsor account already has a pending or current sponsorship.')
            return redirect('sponsorship_detail', pk=sponsorship.pk)
        record_audit_log(request, 'UPDATE', 'Sponsorships', record_id=sponsorship.sponsor_code, details=f'AI matched and approved {child.full_name}')
        if sponsorship.sponsor_id:
            notify_users(
                [sponsorship.sponsor],
                'Sponsorship approved and matched',
                'Your sponsorship request was approved. Complete your first Safepay payment to unlock the child profile and progress tracking.',
                reverse('sponsor_child_detail', kwargs={'pk': child.pk}),
            )
        messages.success(request, f'Request approved. AI matched {child.full_name} to this sponsor.')
    return redirect('sponsorship_detail', pk=sponsorship.pk)


@login_required(login_url='admin_login')
def sponsorship_reject(request, pk):
    if not is_admin_user(request.user):
        return redirect('index')
    sponsorship = get_object_or_404(Sponsorship, pk=pk)
    if request.method == 'POST' and sponsorship.status == 'pending':
        sponsorship.status = 'rejected'
        sponsorship.admin_notes = request.POST.get('admin_notes', '').strip()
        sponsorship.save(update_fields=['status', 'admin_notes'])
        record_audit_log(request, 'UPDATE', 'Sponsorships', record_id=sponsorship.sponsor_code, details='Rejected sponsor request')
        if sponsorship.sponsor_id:
            notify_users(
                [sponsorship.sponsor],
                'Sponsorship request update',
                'Your sponsorship request was not approved. Sign in to view the update or contact the organization.',
                reverse('sponsor_dashboard'),
            )
        messages.success(request, 'Sponsorship request rejected.')
    return redirect('sponsorship_detail', pk=sponsorship.pk)


@login_required(login_url='sponsor_login')
@require_POST
def sponsor_cancel_sponsorship(request, pk):
    profile = getattr(request.user, 'account_profile', None)
    if not profile or profile.role != AccountProfile.ROLE_SPONSOR:
        return HttpResponseForbidden('Only sponsors can end their sponsorship.')

    sponsorship = get_object_or_404(
        Sponsorship.objects.select_related('child'),
        pk=pk,
        sponsor=request.user,
        status='active',
    )
    today = timezone.localdate()
    if not sponsorship.minimum_commitment_end_date:
        messages.error(request, 'Please contact an administrator to confirm the agreement term before ending this sponsorship.')
        return redirect('sponsor_dashboard')
    if today < sponsorship.minimum_commitment_end_date:
        messages.error(
            request,
            f'This sponsorship has a minimum commitment through {sponsorship.minimum_commitment_end_date}.',
        )
        if sponsorship.child_id:
            return redirect('sponsor_child_detail', pk=sponsorship.child_id)
        return redirect('sponsor_dashboard')

    with transaction.atomic():
        sponsorship.status = 'ended'
        sponsorship.ended_at = today
        sponsorship.save(update_fields=['status', 'ended_at'])
        if sponsorship.child_id and not Sponsorship.objects.filter(
            child_id=sponsorship.child_id,
            status='active',
        ).exclude(pk=sponsorship.pk).exists():
            sponsorship.child.sponsor_status = 'available'
            sponsorship.child.save(update_fields=['sponsor_status'])

    record_audit_log(
        request,
        'UPDATE',
        'Sponsorships',
        record_id=sponsorship.sponsor_code,
        details='Sponsor ended the sponsorship after the minimum commitment period',
    )
    notify_users(
        [request.user],
        'Sponsorship ended',
        'Your sponsorship has ended. Thank you for supporting a child through KafalatCare.',
        reverse('sponsor_dashboard'),
    )
    staff_users = [
        conversation.staff.user
        for conversation in sponsorship.conversations.select_related('staff__user')
        if conversation.staff and conversation.staff.user
    ]
    notify_users(
        staff_users,
        'Sponsorship ended',
        'A sponsorship conversation you participated in is now closed.',
        reverse('sponsorship_message_inbox'),
    )
    admins = request.user.__class__.objects.filter(account_profile__role=AccountProfile.ROLE_ADMIN)
    notify_users(
        admins,
        'Sponsorship ended',
        'A sponsor ended a sponsorship after the minimum commitment period.',
        reverse('sponsorship_detail', kwargs={'pk': sponsorship.pk}),
    )
    messages.success(request, 'Your sponsorship has ended.')
    return redirect('sponsor_dashboard')


def _active_sponsorship_conversation_for_user(request, conversation_id):
    conversation = get_object_or_404(
        SponsorshipConversation.objects.select_related(
            'sponsorship__sponsor',
            'sponsorship__child',
            'staff__user',
        ),
        pk=conversation_id,
        sponsorship__status='active',
    )
    sponsor = conversation.sponsorship.sponsor
    staff_user = conversation.staff.user if conversation.staff else None
    profile = getattr(request.user, 'account_profile', None)
    if (
        sponsor
        and request.user.pk == sponsor.pk
        and profile
        and profile.role == AccountProfile.ROLE_SPONSOR
    ):
        if has_verified_sponsorship_payment(conversation.sponsorship):
            return conversation
        raise PermissionError
    if (
        staff_user
        and request.user.pk == staff_user.pk
        and profile
        and profile.role == AccountProfile.ROLE_STAFF
        and conversation.staff.employment_status == 'active'
    ):
        return conversation
    raise PermissionError


def _communication_page_context(request, page_title):
    context = {'page_title': page_title}
    profile = getattr(request.user, 'account_profile', None)
    if profile and profile.role == AccountProfile.ROLE_SPONSOR:
        from accounts.views.sponsor_views import sponsor_dashboard_context

        context.update(sponsor_dashboard_context(request))
        context['page_title'] = page_title
        context['active_section'] = 'communications'
    return context


@login_required(login_url='login')
def sponsorship_message_inbox(request):
    profile = getattr(request.user, 'account_profile', None)
    if profile and profile.role == AccountProfile.ROLE_SPONSOR:
        conversations = SponsorshipConversation.objects.filter(
            sponsorship__sponsor=request.user,
            sponsorship__status='active',
            sponsorship__payment_transactions__status=Payment.STATUS_PAID,
        )
    elif profile and profile.role == AccountProfile.ROLE_STAFF:
        staff_member = StaffMember.objects.filter(
            user=request.user,
            employment_status='active',
        ).first()
        if staff_member is None:
            return HttpResponseForbidden('An active staff profile is required.')
        conversations = SponsorshipConversation.objects.filter(
            staff=staff_member,
            sponsorship__status='active',
        )
    else:
        return HttpResponseForbidden('Only sponsors and active staff can access sponsorship messages.')

    conversations = conversations.select_related(
        'sponsorship__child',
        'sponsorship__sponsor',
        'staff__user',
    ).distinct().annotate(
        unread_message_count=Count(
            'messages',
            filter=Q(messages__read_at__isnull=True) & ~Q(messages__sender=request.user),
        ),
    ).order_by('-updated_at')
    context = _communication_page_context(request, 'Sponsorship Messages')
    context['conversations'] = conversations
    return render(request, 'sponsorships/message_inbox.html', context)


@login_required(login_url='login')
@require_POST
def sponsor_message_send(request, child_id):
    profile = getattr(request.user, 'account_profile', None)
    if not profile or profile.role != AccountProfile.ROLE_SPONSOR:
        return HttpResponseForbidden('Only sponsors can start a sponsorship conversation.')

    sponsorship = get_object_or_404(
        Sponsorship.objects.select_related('child'),
        sponsor=request.user,
        child_id=child_id,
        status='active',
    )
    if not has_verified_sponsorship_payment(sponsorship):
        return HttpResponseForbidden('A verified first sponsorship payment is required to contact staff.')
    form = SponsorMessageForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Select an active staff member and enter a message.')
        return redirect('sponsor_child_detail', pk=child_id)

    staff_member = form.cleaned_data['staff']
    with transaction.atomic():
        conversation, _ = SponsorshipConversation.objects.get_or_create(
            sponsorship=sponsorship,
            staff=staff_member,
        )
        message = SponsorshipMessage.objects.create(
            conversation=conversation,
            sender=request.user,
            body=form.cleaned_data['body'].strip(),
        )
        conversation.updated_at = message.created_at
        conversation.save(update_fields=['updated_at'])

    is_selected_caretaker = (
        is_caretaker(staff_member)
        and sponsorship.child_id is not None
        and sponsorship.child.caretakers.filter(pk=staff_member.pk).exists()
    )
    notify_users(
        [staff_member.user],
        'New message about an assigned child' if is_selected_caretaker else 'New sponsorship message',
        (
            'A sponsor sent you a message about a child assigned to you. Sign in to read it in Child Messages.'
            if is_selected_caretaker
            else 'A sponsor sent you a message. Sign in to reply in the sponsorship message center.'
        ),
        (
            reverse('caretaker_messages')
            if is_selected_caretaker
            else reverse('sponsorship_message_thread', kwargs={'conversation_id': conversation.pk})
        ),
    )
    messages.success(request, 'Your message was sent to the staff member.')
    return redirect('sponsor_message_thread', conversation_id=conversation.pk)


@login_required(login_url='login')
def sponsorship_message_thread(request, conversation_id):
    try:
        conversation = _active_sponsorship_conversation_for_user(request, conversation_id)
    except PermissionError:
        return HttpResponseForbidden('You are not a participant in this conversation.')

    staff_user = conversation.staff.user if conversation.staff else None
    if staff_user is None:
        return HttpResponseForbidden('This conversation has no available staff member.')
    recipient = (
        staff_user
        if request.user.pk == conversation.sponsorship.sponsor_id
        else conversation.sponsorship.sponsor
    )
    if recipient is None:
        return HttpResponseForbidden('This conversation has no available recipient.')

    if request.method == 'POST':
        body = request.POST.get('body', '').strip()
        if not body or len(body) > 4000:
            messages.error(request, 'Enter a message of 1 to 4000 characters.')
        else:
            sent_message = SponsorshipMessage.objects.create(
                conversation=conversation,
                sender=request.user,
                body=body,
            )
            conversation.updated_at = sent_message.created_at
            conversation.save(update_fields=['updated_at'])
            recipient_profile = getattr(recipient, 'account_profile', None)
            thread_url = (
                reverse('sponsor_message_thread', kwargs={'conversation_id': conversation.pk})
                if recipient_profile and recipient_profile.role == AccountProfile.ROLE_SPONSOR
                else reverse('sponsorship_message_thread', kwargs={'conversation_id': conversation.pk})
            )
            notify_users(
                [recipient],
                'New sponsorship message',
                'You have a new message in a sponsorship conversation. Sign in to read and reply.',
                thread_url,
            )
            messages.success(request, 'Your message was sent.')
            if request.user.pk == conversation.sponsorship.sponsor_id:
                return redirect('sponsor_message_thread', conversation_id=conversation.pk)
            return redirect('sponsorship_message_thread', conversation_id=conversation.pk)

    conversation.messages.exclude(sender=request.user).filter(read_at__isnull=True).update(
        read_at=timezone.now(),
    )
    context = _communication_page_context(request, 'Sponsorship Conversation')
    context.update({
        'conversation': conversation,
        'conversation_messages': conversation.messages.select_related('sender'),
    })
    return render(request, 'sponsorships/message_thread.html', context)


@login_required(login_url='login')
def notification_list(request):
    notifications = Notification.objects.filter(recipient=request.user)
    page_obj = Paginator(notifications, 30).get_page(request.GET.get('page'))
    context = _communication_page_context(request, 'Notifications')
    context['page_obj'] = page_obj
    return render(request, 'sponsorships/notification_list.html', context)


@login_required(login_url='login')
@require_POST
def notification_mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=['read_at'])
    return redirect('notification_list')
