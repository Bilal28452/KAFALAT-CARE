#!/usr/bin/env python
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
directories = [
    REPO_ROOT / 'frontend' / 'templates' / 'children',
    REPO_ROOT / 'frontend' / 'templates' / 'sponsorships',
    REPO_ROOT / 'frontend' / 'templates' / 'staff_management',
    REPO_ROOT / 'frontend' / 'templates' / 'donations',
]

for dir_path in directories:
    dir_path.mkdir(parents=True, exist_ok=True)
    print(f"Created: {dir_path}")

print("All template directories created successfully!")
