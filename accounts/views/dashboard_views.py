from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse

from .auth_views import is_admin_user
from .nav_views import get_dashboard_nav_items, get_dashboard_management_sections
from .. import dashboard as accounts_dashboard
from children import dashboard as children_dashboard
from donations import dashboard as donations_dashboard
from sponsorships import dashboard as sponsorships_dashboard
from staff_management import dashboard as staff_dashboard


def determine_active_section(request):
    path = request.path
    
    # Staff paths FIRST (to avoid conflicts with children)
    if path.startswith('/staff/attendance') or path.startswith('/staff_management/attendance'):
        return 'staff'
    if path.startswith('/staff/payroll') or path.startswith('/staff_management/payroll'):
        return 'staff'
    if path.startswith('/staff/leaves') or path.startswith('/staff_management/leaves'):
        return 'staff'
    if path.startswith('/staff/') or path.startswith('/staff_management/'):
        return 'staff'
    
    # Meals section
    if path.startswith('/meals/'):
        return 'meals'
    
    # Education paths
    if path.startswith('/children/education'):
        return 'education'
    if path.startswith('/children/courses/'):
        return 'education'
    if path.startswith('/children/teachers/'):
        return 'education'
    if path.startswith('/children/attendance/'):
        return 'education'
    if path.startswith('/children/results/'):
        return 'education'
    
    # Children paths
    if path.startswith('/children/health'):
        return 'health'
    if path.startswith('/children/'):
        return 'children'
    
    # Other sections
    if path.startswith('/donations/'):
        return 'donations'
    if path.startswith('/sponsorships/'):
        return 'sponsorships'
    if path.startswith('/accounts/users/'):
        return 'users'

    # Default fallback
    management_sections = get_dashboard_management_sections(request)
    valid_sections = {'overview', 'reports', 'ai'} | {section['id'] for section in management_sections}
    active_section = request.GET.get('section', 'overview')
    
    return active_section if active_section in valid_sections else 'overview'


def dashboard_context(request):
    admin_name = request.user.get_full_name() or request.user.username or 'Admin'
    initials = ''.join(part[0] for part in admin_name.split()[:2]).upper() or 'AD'

    management_sections = get_dashboard_management_sections(request)
    active_section = determine_active_section(request)
    nav_items = get_dashboard_nav_items(request)
    active_nav_item = next((item for item in nav_items if item['id'] == active_section), nav_items[0])
    active_management_section = next((section for section in management_sections if section['id'] == active_section), None)
    
    child_stats = children_dashboard.stats()
    staff_stats = staff_dashboard.stats()
    sponsorship_stats = sponsorships_dashboard.stats()
    donation_stats = donations_dashboard.stats()

    return {
        'page_title': active_nav_item['label'],
        'admin_name': admin_name,
        'admin_role': 'Administrator',
        'user_initials': initials[:2],
        'active_section': active_section,
        'active_nav_item': active_nav_item,
        'active_management_section': active_management_section,
        'nav_items': nav_items,
        'stats': [
            {'label': 'Total Children', 'value': child_stats['total_children'], 'change': f"{child_stats['sponsored_children']} sponsored", 'change_icon': 'bi bi-heart', 'icon': 'bi bi-people-fill', 'icon_class': 'icon-emerald'},
            {'label': 'Active Staff', 'value': staff_stats['active_staff'], 'change': 'From staff database', 'change_icon': 'bi bi-check-circle', 'icon': 'bi bi-person-badge', 'icon_class': 'icon-blue'},
            {'label': 'Monthly Donations', 'value': f"PKR {donation_stats['monthly_donations']:,.0f}", 'change': 'Current month', 'change_icon': 'bi bi-cash-coin', 'icon': 'bi bi-gift', 'icon_class': 'icon-gold'},
            {'label': 'Active Sponsors', 'value': sponsorship_stats['active_sponsors'], 'change': 'Active sponsorships', 'change_icon': 'bi bi-check-circle', 'icon': 'bi bi-heart', 'icon_class': 'icon-green'},
            {'label': 'Health Alerts', 'value': child_stats['health_alerts'], 'change': 'Require attention', 'change_icon': 'bi bi-exclamation-triangle', 'icon': 'bi bi-heart-pulse', 'icon_class': 'icon-danger'},
        ],
        'quick_actions': [
            {'label': 'Add Child', 'icon': 'bi bi-plus-circle', 'url': reverse('child_create')},
            {'label': 'Add Health Record', 'icon': 'bi bi-heart-pulse', 'url': reverse('health_record_create')},
            {'label': 'Add Education Record', 'icon': 'bi bi-book', 'url': reverse('education_record_create')},
            {'label': 'Add Staff', 'icon': 'bi bi-person-plus', 'url': reverse('staff_create')},
            {'label': 'Match Sponsor', 'icon': 'bi bi-heart-fill', 'url': reverse('sponsorship_create')},
            {'label': 'Record Donation', 'icon': 'bi bi-gift', 'url': reverse('donation_create')},
            {'label': 'Generate Reports', 'icon': 'bi bi-file-earmark-bar-graph', 'url': '?section=reports'},
            {'label': 'AI Risk Detection', 'icon': 'bi bi-shield-check', 'url': '?section=ai'},
        ],
        'management_sections': management_sections,
        'reports': [
            {'label': 'Monthly Progress Report', 'icon': 'bi bi-file-earmark-pdf', 'url': '#'},
            {'label': 'Children Demographics', 'icon': 'bi bi-pie-chart', 'url': '?section=children'},
            {'label': 'Health Summary Report', 'icon': 'bi bi-heart-pulse', 'url': '?section=health'},
            {'label': 'Education Performance', 'icon': 'bi bi-graph-up', 'url': '?section=education'},
            {'label': 'Financial Report', 'icon': 'bi bi-cash-coin', 'url': '?section=donations'},
            {'label': 'Sponsorship Impact', 'icon': 'bi bi-heart', 'url': '?section=sponsorships'},
            {'label': 'Staff Performance', 'icon': 'bi bi-person-badge', 'url': '?section=staff'},
            {'label': 'Annual Summary', 'icon': 'bi bi-calendar-check', 'url': '#'},
        ],
        'ai_tools': [
            {'label': 'Child Risk Detection', 'icon': 'bi bi-shield-check', 'url': '#'},
            {'label': 'Intelligent Sponsor Matching', 'icon': 'bi bi-heart-handshake', 'url': '?section=sponsorships'},
            {'label': 'Health Pattern Analysis', 'icon': 'bi bi-activity', 'url': '?section=health'},
            {'label': 'Education Trend Prediction', 'icon': 'bi bi-graph-up', 'url': '?section=education'},
            {'label': 'Donation Forecasting', 'icon': 'bi bi-cash-stack', 'url': '?section=donations'},
            {'label': 'Smart Document Search', 'icon': 'bi bi-search', 'url': '?section=overview'},
            {'label': 'Automated Report Generator', 'icon': 'bi bi-file-earmark-text', 'url': '?section=reports'},
            {'label': 'Sentiment Analysis', 'icon': 'bi bi-chat-dots', 'url': '#'},
        ],
    }


@login_required(login_url='admin_login')
def dashboard(request):
    if not is_admin_user(request.user):
        messages.error(request, 'Only admin accounts can access the admin dashboard.')
        return redirect('index')
    
    accounts_dashboard.record_audit_log(
        request,
        action='VIEW',
        module='Dashboard',
        details=f"Viewed {request.GET.get('section', 'overview')} dashboard section",
    )
    
    return render(request, 'accounts/admin_dashboard.html', dashboard_context(request))