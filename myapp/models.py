from django.db import models
from django.contrib.auth.models import AbstractUser

# User model for secure authentication
class User(AbstractUser):
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    email = models.EmailField(unique=True)
    USER_TYPES = (
        ('hod', 'Head of Department'),
        ('admin', 'Admin'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPES)
    
    # Unified Staff Fields
    name = models.CharField(max_length=100, blank=True, null=True)
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='staff')
    phone = models.CharField(max_length=100, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        role_str = dict(self.USER_TYPES).get(self.user_type, 'User')
        if self.name:
            return f"{role_str} {self.name} - {self.email}"
        return self.email


# Department model to group students and HODs
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Student(models.Model):
    student_id = models.CharField(max_length=12, unique=True, null=True, blank=True)
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='students')

    # Student data (features for prediction based on Student_Performance.csv)
    age = models.IntegerField(null=True)
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], null=True)
    school_type = models.CharField(max_length=10, choices=[('public', 'Public'), ('private', 'Private')], null=True)
    
    # Education & Study Habits
    parent_education = models.CharField(max_length=50, choices=[
        ('no formal', 'No Formal'),
        ('high school', 'High School'),
        ('diploma', 'Diploma'),
        ('graduate', 'Graduate'),
        ('post graduate', 'Post Graduate'),
        ('phd', 'PhD')
    ], null=True)
    
    study_hours = models.FloatField(null=True, help_text="Weekly study hours")
    attendance_percentage = models.FloatField(null=True)
    internet_access = models.CharField(max_length=5, choices=[('yes', 'Yes'), ('no', 'No')], null=True)
    travel_time = models.CharField(max_length=20, choices=[
        ('<15 min', '<15 min'),
        ('15-30 min', '15-30 min'),
        ('30-60 min', '30-60 min'),
        ('>60 min', '>60 min')
    ], null=True)
    
    extra_activities = models.CharField(max_length=5, choices=[('yes', 'Yes'), ('no', 'No')], null=True)
    study_method = models.CharField(max_length=20, choices=[
        ('notes', 'Notes'),
        ('textbook', 'Textbook'),
        ('group study', 'Group Study'),
        ('coaching', 'Coaching'),
        ('online videos', 'Online Videos'),
        ('mixed', 'Mixed')
    ], null=True)

    # Performance Metrics
    math_score = models.FloatField(null=True)
    science_score = models.FloatField(null=True)
    english_score = models.FloatField(null=True)
    overall_score = models.FloatField(null=True)
    final_grade = models.CharField(max_length=5, choices=[
        ('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D'), ('e', 'E'), ('f', 'F')
    ], null=True)

    address = models.CharField(max_length=255, null=True, blank=True)
    result = models.CharField(max_length=100, null=True, blank=True)
    risk_level = models.CharField(max_length=20, choices=[('Low', 'Low Risk'), ('Medium', 'Medium Risk'), ('High', 'High Risk')], default='Low')
    last_prediction_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.student_id})"

    def get_ml_features(self, meta):
        """
        Extracts and encodes features for ML prediction based on model metadata.
        """
        def get_encoded_value(col, val):
            classes = meta['encoders'].get(col, [])
            val = str(val).lower() if val else ""
            if val in classes:
                return classes.index(val)
            return 0

        return [
            get_encoded_value('gender', self.gender),
            get_encoded_value('school_type', self.school_type),
            get_encoded_value('parent_education', self.parent_education),
            get_encoded_value('internet_access', self.internet_access),
            get_encoded_value('travel_time', self.travel_time),
            get_encoded_value('extra_activities', self.extra_activities),
            get_encoded_value('study_method', self.study_method),
            self.age or 0,
            self.study_hours or 0,
            self.attendance_percentage or 0
        ]

# Intervention model to track actions taken for at-risk students
class Intervention(models.Model):
    INTERVENTION_TYPES = (
        ('Meeting', 'Parent-Teacher Meeting'),
        ('Extra Class', 'Additional Tutoring'),
        ('Counseling', 'School Counseling'),
        ('Peer Support', 'Peer Mentoring'),
        ('Other', 'Other'),
    )
    STATUS_CHOICES = (
        ('Planned', 'Planned'),
        ('Ongoing', 'Ongoing'),
        ('Completed', 'Completed'),
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='interventions')
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='interventions_managed', limit_choices_to={'user_type__in': ['hod', 'admin']})
    action_taken = models.TextField()
    intervention_type = models.CharField(max_length=50, choices=INTERVENTION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Planned')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Intervention for {self.student.name} - {self.intervention_type}"

