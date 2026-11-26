from .views import get_dashboard_nav_items, get_dashboard_management_sections, determine_active_section
from sponsorships.communication_context import communication_badges


def dashboard_nav(request):
    nav_items = get_dashboard_nav_items()
    active_section = determine_active_section(request)
    active_nav_item = next((item for item in nav_items if item['id'] == active_section), nav_items[0])
    # Pass request to get_dashboard_management_sections
    active_management_section = next((section for section in get_dashboard_management_sections(request) if section['id'] == active_section), None)
    
    if request.user.is_authenticated:
        admin_name = request.user.get_full_name() or request.user.username or 'Admin'
        initials = ''.join(part[0] for part in admin_name.split()[:2]).upper() or 'AD'
    else:
        admin_name = 'Guest'
        initials = 'GU'
    
    path = request.path
    show_dashboard_nav = any(
        path.startswith(prefix) for prefix in (
            '/children/', '/donations/', '/sponsorships/', '/staff_management/', '/dashboard',
        )
    ) and request.user.is_authenticated

    return {
        **communication_badges(request.user),
        'show_dashboard_nav': show_dashboard_nav,
        'nav_items': nav_items,
        'active_section': active_section,
        'active_nav_item': active_nav_item,
        'active_management_section': active_management_section,
        'page_title': active_nav_item['label'],
        'admin_name': admin_name,
        'admin_role': 'Administrator',
        'user_initials': initials[:2],
    }