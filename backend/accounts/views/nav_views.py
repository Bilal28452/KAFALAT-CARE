from django.urls import reverse
from django.utils.functional import lazy

# Use lazy reverse to avoid circular imports
reverse_lazy = lazy(reverse, str)


def get_dashboard_nav_items(request=None):
    """Get navigation items with active state detection"""
    
    # Get current path if request is provided
    current_path = request.path if request else ''
    
    # Dashboard staff URL
    dashboard_staff_url = reverse('dashboard') + '?section=staff'
    
    # Define submenu URLs for education section
    education_submenu_urls = [
        reverse('education_dashboard'),
        reverse('education_record_list'),
        reverse('course_list'),
        reverse('teacher_list'),
        reverse('attendance'),
        reverse('education_result_list'),
        reverse('education_class_overview'),
    ]
    payment_history_urls = [
        reverse('admin_donation_payment_history'),
        reverse('admin_sponsorship_payment_history'),
    ]
    
    nav_items = [
        {'id': 'overview', 'label': 'Overview', 'icon': 'bi bi-speedometer2', 'url': reverse('dashboard') + '?section=overview'},
        {'id': 'children', 'label': 'Children', 'icon': 'bi bi-people-fill', 'url': reverse('dashboard') + '?section=children'},
        {'id': 'health', 'label': 'Health', 'icon': 'bi bi-heart-pulse', 'url': reverse('dashboard') + '?section=health'},
        {
            'id': 'education',
            'label': 'Education',
            'icon': 'bi bi-book',
            'subitems': [
                {'label': 'Education Dashboard', 'icon': 'bi bi-speedometer2', 'url': reverse('education_dashboard')},
                {'label': 'Education Records', 'icon': 'bi bi-file-earmark-text', 'url': reverse('education_record_list')},
                {'label': 'Courses', 'icon': 'bi bi-journal-bookmark-fill', 'url': reverse('course_list')},
                {'label': 'Teachers', 'icon': 'bi bi-person-badge', 'url': reverse('teacher_list')},
                {'label': 'Attendance', 'icon': 'bi bi-calendar-check', 'url': reverse('attendance')},
                {'label': 'Results', 'icon': 'bi bi-clipboard-data', 'url': reverse('education_result_list')},
                {'label': 'Class Overview', 'icon': 'bi bi-people', 'url': reverse('education_class_overview')},
            ],
            'is_active': current_path in education_submenu_urls or current_path.startswith('/children/')
        },

       {
            'id': 'staff',
            'label': 'Staff',
            'icon': 'bi bi-person-badge',
            'url': reverse('dashboard') + '?section=staff',
            'subitems': [
                {'label': 'Staff Dashboard', 'icon': 'bi bi-speedometer2', 'url': reverse('dashboard') + '?section=staff'},
                {'label': 'Attendance', 'icon': 'bi bi-calendar-check', 'url': reverse('staff_attendance')},
                {'label': 'Salary & Payroll', 'icon': 'bi bi-cash-stack', 'url': reverse('staff_payroll')},
                {'label': 'Leave Requests', 'icon': 'bi bi-envelope-paper', 'url': reverse('staff_leaves')},
            ],
            'is_active': (
                current_path == reverse('dashboard') + '?section=staff' or
                current_path.startswith('/staff/attendance') or
                current_path.startswith('/staff/payroll') or
                current_path.startswith('/staff/leaves') or
                current_path.startswith('/staff/') or
                current_path.startswith('/staff_management/')
            )
        },

        {
            'id': 'meals',
            'label': 'Meals',
            'icon': 'bi bi-egg-fried',
            'url': reverse('dashboard') + '?section=meals',
            'subitems': [
                {'label': 'Daily Log', 'icon': 'bi bi-pencil-square', 'url': reverse('daily_log')},
                {'label': 'Meal Schedule', 'icon': 'bi bi-calendar-week', 'url': reverse('meal_schedule')},
                {'label': 'Meal Reports', 'icon': 'bi bi-bar-chart', 'url': reverse('meal_reports')},
            ],
            'is_active': (
                current_path.startswith('/meals/daily-log') or
                current_path.startswith('/meals/schedule') or
                current_path.startswith('/meals/reports') or
                current_path.startswith('/meals/')
            )
        },


        {'id': 'sponsorships', 'label': 'Sponsorships', 'icon': 'bi bi-heart', 'url': reverse('dashboard') + '?section=sponsorships'},
        {'id': 'donations', 'label': 'Donations', 'icon': 'bi bi-gift', 'url': reverse('dashboard') + '?section=donations'},
        {
            'id': 'payment_history',
            'label': 'Payment History',
            'icon': 'bi bi-credit-card',
            'subitems': [
                {
                    'label': 'Donations',
                    'icon': 'bi bi-gift',
                    'url': reverse('admin_donation_payment_history'),
                },
                {
                    'label': 'Sponsorships',
                    'icon': 'bi bi-heart',
                    'url': reverse('admin_sponsorship_payment_history'),
                },
            ],
            'is_active': current_path in payment_history_urls,
        },
        {'id': 'reports', 'label': 'Reports', 'icon': 'bi bi-bar-chart', 'url': reverse('dashboard') + '?section=reports'},
        {'id': 'ai', 'label': 'AI Tools', 'icon': 'bi bi-robot', 'url': reverse('dashboard') + '?section=ai'},
        {'id': 'users', 'label': 'Users', 'icon': 'bi bi-shield-lock', 'url': reverse('user_list')},
        {'id': 'audit', 'label': 'Audit Logs', 'icon': 'bi bi-file-earmark-text', 'url': reverse('dashboard') + '?section=audit'},
    ]
    
    # Mark active subitems based on current path
    if request:
        for item in nav_items:
            if 'subitems' in item:
                for sub in item['subitems']:
                    if current_path == sub['url']:
                        sub['active'] = True
    
    return nav_items


def get_dashboard_management_sections(request):
    from children import dashboard as children_dashboard
    from donations import dashboard as donations_dashboard
    from sponsorships import dashboard as sponsorships_dashboard
    from staff_management import dashboard as staff_dashboard
    from .. import dashboard as accounts_dashboard

    return [
        children_dashboard.children_section(),
        children_dashboard.health_section(),
        children_dashboard.education_section(),
        staff_dashboard.staff_section(request),
        sponsorships_dashboard.sponsorships_section(),
        donations_dashboard.donations_section(),
        accounts_dashboard.users_section(),
        accounts_dashboard.audit_section(),
    ]