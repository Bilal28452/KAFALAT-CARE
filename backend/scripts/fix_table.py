import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kafalatsystem.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute('PRAGMA foreign_keys=OFF')

    # Rebuild the education result table with the current StaffMember foreign key.
    # This repairs databases created from an earlier schema that referenced a removed children_teacher table.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS children_educationresult_fixed (
            id integer PRIMARY KEY AUTOINCREMENT,
            term varchar(80) NOT NULL,
            score decimal NULL,
            grade varchar(20) NOT NULL,
            remarks text NOT NULL,
            created_at datetime NOT NULL,
            updated_at datetime NOT NULL,
            child_id bigint NOT NULL,
            course_id bigint NULL,
            teacher_id bigint NULL,
            FOREIGN KEY (child_id) REFERENCES children_child (id),
            FOREIGN KEY (course_id) REFERENCES children_course (id),
            FOREIGN KEY (teacher_id) REFERENCES staff_management_staffmember (id)
        )
    ''')

    if cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='children_educationresult'").fetchone():
        cursor.execute('''
            INSERT INTO children_educationresult_fixed
            (id, term, score, grade, remarks, created_at, updated_at, child_id, course_id, teacher_id)
            SELECT id, term, score, grade, remarks, created_at, updated_at, child_id, course_id, teacher_id
            FROM children_educationresult
        ''')
        cursor.execute('DROP TABLE children_educationresult')
        cursor.execute('ALTER TABLE children_educationresult_fixed RENAME TO children_educationresult')

    # Create the attendance table if a partially-applied migration left it absent.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS children_attendance (
            id integer PRIMARY KEY AUTOINCREMENT,
            date date NOT NULL,
            status varchar(20) NOT NULL,
            remarks text NOT NULL,
            marked_by varchar(120) NOT NULL,
            created_at datetime NOT NULL,
            updated_at datetime NOT NULL,
            child_id bigint NOT NULL,
            FOREIGN KEY (child_id) REFERENCES children_child (id)
        )
    """)

    cursor.execute('PRAGMA foreign_keys=ON')

print('Database tables repaired successfully.')