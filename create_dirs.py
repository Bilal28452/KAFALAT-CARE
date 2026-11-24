#!/usr/bin/env python
import os
import sys

# Create all necessary directories
directories = [
    r'e:\KafalatCare\children\templates\children',
    r'e:\KafalatCare\sponsorships\templates\sponsorships',
    r'e:\KafalatCare\staff_management\templates\staff_management',
    r'e:\KafalatCare\donations\templates\donations',
]

for dir_path in directories:
    os.makedirs(dir_path, exist_ok=True)
    print(f"Created: {dir_path}")

print("All template directories created successfully!")
