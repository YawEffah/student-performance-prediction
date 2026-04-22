import os
import django
from django.contrib.auth.hashers import make_password

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from myapp.models import User, Department, HOD, Admin, Student

def populate():
    # Clear existing data
    User.objects.all().delete()
    Department.objects.all().delete()
    Student.objects.all().delete()

    # Create Departments
    cs = Department.objects.create(name="Computer Science", description="Department of CS")
    math = Department.objects.create(name="Mathematics", description="Department of Math")

    # Create Admin
    admin_user = User.objects.create(
        email="admin@edupredict.com",
        password=make_password("admin123"),
        user_type="admin",
        is_staff=True,
        is_superuser=True
    )
    Admin.objects.create(
        user=admin_user,
        name="John",
        familyname="Admin",
        phone="123456789",
        address="Main St",
        hiredate="2020-01-01",
        department=cs
    )

    # Create HOD
    hod_user = User.objects.create(
        email="hod_cs@edupredict.com",
        password=make_password("hod123"),
        user_type="hod"
    )
    HOD.objects.create(
        user=hod_user,
        name="Jane",
        familyname="HOD",
        department=cs,
        phone="987654321",
        address="CS Building",
        hiredate="2021-01-01"
    )

    # Create Student (Now without User relationship)
    Student.objects.create(
        student_id="STU001",
        name="Alice",
        department=cs,
        age=20,
        gender="female",
        school_type="public",
        parent_education="graduate",
        study_hours=15.0,
        attendance_percentage=85.0,
        internet_access="yes",
        travel_time="<15 min",
        extra_activities="yes",
        study_method="notes",
        overall_score=75.0,
        final_grade="b"
    )

    print("Database populated successfully (No student user type)!")

if __name__ == '__main__':
    populate()
