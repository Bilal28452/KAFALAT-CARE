"""Create template structure management command"""
from django.core.management.base import BaseCommand
from pathlib import Path
import os


class Command(BaseCommand):
    help = 'Creates all necessary template directories and files for KafalatCare'

    def handle(self, *args, **options):
        BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
        
        template_structure = {
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
        
        for app, templates in template_structure.items():
            app_template_dir = BASE_DIR / app / 'templates' / app
            app_template_dir.mkdir(parents=True, exist_ok=True)
            self.stdout.write(self.style.SUCCESS(f'✓ Created: {app_template_dir}'))
            
            for template in templates:
                template_path = app_template_dir / template
                if not template_path.exists():
                    template_path.touch()
                    self.stdout.write(f'  ✓ Created: {template}')
        
        self.stdout.write(
            self.style.SUCCESS('\n✓ All template directories created successfully!')
        )
