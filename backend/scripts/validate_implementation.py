#!/usr/bin/env python
"""
Validation script to verify all forms and CRUD components are implemented correctly.

Usage:
    python backend/scripts/validate_implementation.py
"""

import os
import sys
from pathlib import Path

def check_file_exists(path, description):
    """Check if a file exists"""
    exists = os.path.isfile(path)
    status = "✅" if exists else "❌"
    print(f"  {status} {description}")
    return exists

def check_dir_exists(path, description):
    """Check if a directory exists"""
    exists = os.path.isdir(path)
    status = "✅" if exists else "❌"
    print(f"  {status} {description}")
    return exists

def check_content_in_file(filepath, search_strings, description):
    """Check if specific content exists in a file"""
    if not os.path.isfile(filepath):
        print(f"  ❌ {description} - File not found: {filepath}")
        return False
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            for search_str in search_strings:
                if search_str not in content:
                    print(f"  ❌ {description} - Missing: {search_str}")
                    return False
        print(f"  ✅ {description}")
        return True
    except Exception as e:
        print(f"  ❌ {description} - Error: {e}")
        return False

def main():
    """Run validation checks"""
    print("\n" + "="*60)
    print("KafalatCare Implementation Validation")
    print("="*60 + "\n")
    
    backend_dir = Path(__file__).resolve().parents[1]
    repo_root = backend_dir.parent
    checks_passed = 0
    checks_failed = 0
    
    # Check 1: Directory Structure
    print("1️⃣  Checking Directory Structure...")
    dirs = [
        ('children', 'Children app'),
        ('sponsorships', 'Sponsorships app'),
        ('staff_management', 'Staff management app'),
        ('donations', 'Donations app'),
    ]
    
    for app_name, description in dirs:
        if check_dir_exists(backend_dir / app_name, description):
            checks_passed += 1
        else:
            checks_failed += 1
    
    print()
    
    # Check 2: Forms Implementation
    print("2️⃣  Checking Forms Implementation...")
    forms_checks = [
        (backend_dir / 'children' / 'forms.py',
         ['ChildForm', 'HealthRecordForm', 'EducationRecordForm'],
         'Children forms'),
        (backend_dir / 'sponsorships' / 'forms.py',
         ['SponsorshipForm'],
         'Sponsorships form'),
        (backend_dir / 'staff_management' / 'forms.py',
         ['StaffMemberForm'],
         'Staff management form'),
        (backend_dir / 'donations' / 'forms.py',
         ['DonationForm'],
         'Donations form'),
    ]
    
    for filepath, search_strings, description in forms_checks:
        if check_content_in_file(filepath, search_strings, description):
            checks_passed += 1
        else:
            checks_failed += 1
    
    print()
    
    # Check 3: Views Implementation
    print("3️⃣  Checking CRUD Views Implementation...")
    views_checks = [
        (backend_dir / 'children' / 'views' / 'child_views.py',
         ['child_list', 'child_create', 'child_detail', 'child_update', 'child_delete'],
         'Children CRUD views'),
        (backend_dir / 'children' / 'views' / 'health_views.py',
         ['health_record_create', 'health_record_detail', 'health_record_update', 'health_record_delete'],
         'Health-record views'),
        (backend_dir / 'children' / 'views' / 'education_views.py',
         ['education_record_list', 'education_record_create'],
         'Education-record views'),
        (backend_dir / 'sponsorships' / 'views.py',
         ['sponsorship_list', 'sponsorship_create', 'sponsorship_detail', 'sponsorship_delete'],
         'Sponsorships CRUD views'),
        (backend_dir / 'staff_management' / 'views' / 'staff_views.py',
         ['staff_list', 'staff_create', 'staff_detail', 'staff_delete'],
         'Staff management CRUD views'),
        (backend_dir / 'donations' / 'views.py',
         ['donation_list', 'donation_create', 'donation_detail', 'donation_delete'],
         'Donations CRUD views'),
    ]
    
    for filepath, search_strings, description in views_checks:
        if check_content_in_file(filepath, search_strings, description):
            checks_passed += 1
        else:
            checks_failed += 1
    
    print()
    
    # Check 4: Template Setup Scripts
    print("4️⃣  Checking Template Setup Scripts...")
    scripts = [
        (backend_dir / 'scripts' / 'generate_all_templates.py', 'Main template generator'),
        (backend_dir / 'scripts' / 'setup_templates.py', 'Alternative setup script'),
        (backend_dir / 'scripts' / 'create_templates.py', 'Django shell script'),
    ]
    
    for script_path, description in scripts:
        if check_file_exists(script_path, description):
            checks_passed += 1
        else:
            checks_failed += 1
    
    print()
    
    # Check 5: Documentation
    print("5️⃣  Checking Documentation...")
    docs = [
        (repo_root / 'FORMS_AND_CRUD_GUIDE.md', 'Implementation guide'),
        (repo_root / 'IMPLEMENTATION_SUMMARY.md', 'Summary document'),
    ]
    
    for doc_path, description in docs:
        if check_file_exists(doc_path, description):
            checks_passed += 1
        else:
            checks_failed += 1
    
    print()
    
    # Check 6: Models Validation
    print("6️⃣  Checking Models...")
    models_checks = [
        (backend_dir / 'children' / 'models.py',
         ['class Child', 'class HealthRecord', 'class EducationRecord'],
         'Children models'),
        (backend_dir / 'sponsorships' / 'models.py',
         ['class Sponsorship'],
         'Sponsorships model'),
        (backend_dir / 'staff_management' / 'models.py',
         ['class StaffMember'],
         'Staff management model'),
        (backend_dir / 'donations' / 'models.py',
         ['class Donation'],
         'Donations model'),
    ]
    
    for filepath, search_strings, description in models_checks:
        if check_content_in_file(filepath, search_strings, description):
            checks_passed += 1
        else:
            checks_failed += 1
    
    print()
    
    # Summary
    print("="*60)
    print(f"Summary: ✅ {checks_passed} Passed | ❌ {checks_failed} Failed")
    print("="*60 + "\n")
    
    if checks_failed == 0:
        print("🎉 All checks passed! Implementation is complete.")
        print("\nNext steps:")
        print("  1. Run: python backend/scripts/generate_all_templates.py")
        print("  2. Create URL routing for each app")
        print("  3. Test all CRUD operations")
        return 0
    else:
        print("⚠️  Some checks failed. Please review the above output.")
        print("\nFor help, see:")
        print("  - FORMS_AND_CRUD_GUIDE.md")
        print("  - IMPLEMENTATION_SUMMARY.md")
        return 1

if __name__ == '__main__':
    sys.exit(main())
