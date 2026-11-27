from accounts.models import AccountProfile

from .models import StaffMember


def get_active_staff_member(user):
    if not user.is_authenticated:
        return None

    is_staff_account = AccountProfile.objects.filter(
        user=user,
        role=AccountProfile.ROLE_STAFF,
    ).exists()
    if not is_staff_account:
        return None

    return StaffMember.objects.filter(
        user=user,
        employment_status='active',
    ).first()


def is_teacher(staff_member):
    return staff_member is not None and 'teacher' in staff_member.position.casefold()


def is_doctor(staff_member):
    return staff_member is not None and 'doctor' in staff_member.position.casefold()


def is_caretaker(staff_member):
    if staff_member is None:
        return False
    position = staff_member.position.casefold().replace(' ', '').replace('-', '').replace('_', '')
    return 'caretaker' in position or 'caregiver' in position
