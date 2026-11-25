"""
Django management command to generate all template structure for KafalatCare

Usage: python backend/manage.py shell < backend/scripts/create_templates.py
Or: python backend/manage.py create_templates
"""

import os
from pathlib import Path

def create_template_structure():
    """Create all necessary template directories and files"""
    
    BASE_DIR = Path(__file__).resolve().parents[2]
    
    # Define all template directories needed
    template_dirs = {
        'children': [
            'child_form.html',
            'child_list.html',
            'child_detail.html',
            'child_confirm_delete.html',
            'health_record_form.html',
            'health_record_list.html',
            'health_record_detail.html',
            'health_record_confirm_delete.html',
            'education_record_form.html',
            'education_record_list.html',
            'education_record_detail.html',
            'education_record_confirm_delete.html',
        ],
        'sponsorships': [
            'sponsorship_form.html',
            'sponsorship_list.html',
            'sponsorship_detail.html',
            'sponsorship_confirm_delete.html',
        ],
        'staff_management': [
            'staff_form.html',
            'staff_list.html',
            'staff_detail.html',
            'staff_confirm_delete.html',
        ],
        'donations': [
            'donation_form.html',
            'donation_list.html',
            'donation_detail.html',
            'donation_confirm_delete.html',
        ],
    }
    
    # Create template structure
    for app, templates in template_dirs.items():
        app_template_dir = BASE_DIR / 'frontend' / 'templates' / app
        app_template_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created: {app_template_dir}")
        
        for template in templates:
            template_path = app_template_dir / template
            if not template_path.exists():
                template_path.touch()
                print(f"  Created: {template_path}")

if __name__ == '__main__':
    create_template_structure()
    print("\n✓ All template directories and files created successfully!")
