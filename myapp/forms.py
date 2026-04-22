from django import forms
from django.contrib.auth.hashers import make_password
from .models import Student, User, Department, Intervention


class UserForm(forms.ModelForm):
    """Form for creating a new staff account (email + password only)."""
    class Meta:
        model = User
        fields = ['email', 'password', 'user_type']
        widgets = {
            'password': forms.PasswordInput(),
            'user_type': forms.HiddenInput(),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        # Auto-set username from email to satisfy the unique username constraint
        user.username = self.cleaned_data['email']
        user.password = make_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description']


# Form for Admins registering new staff (No password fields here, password is in UserForm)
class StaffRegistrationForm(forms.ModelForm):
    """Profile fields for initial registration."""
    class Meta:
        model = User
        fields = ['name', 'phone', 'department']


# Form for users updating their own profile (Includes password fields)
class StaffProfileUpdateForm(forms.ModelForm):
    """Profile fields plus optional password change."""
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Leave blank to keep current password'}),
        required=False,
        label="New Password"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm your new password'}),
        required=False,
        label="Confirm Password"
    )

    class Meta:
        model = User
        fields = ['name', 'phone', 'department']

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password and new_password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get("new_password")
        if new_password:
            user.password = make_password(new_password)
        if commit:
            user.save()
        return user
       

class StaffUpdateForm(forms.ModelForm):
    """Full update form for editing an existing staff member's details."""
    class Meta:
        model = User
        fields = ['email', 'name', 'phone', 'department', 'user_type']
        widgets = {
            'user_type': forms.Select(choices=User.USER_TYPES),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        # Keep username in sync with email
        user.username = user.email
        if commit:
            user.save()
        return user


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'student_id', 'name', 'department', 'age', 'gender',
            'school_type', 'parent_education', 'study_hours', 'attendance_percentage',
            'internet_access', 'travel_time', 'extra_activities', 'study_method',
            'math_score', 'science_score', 'english_score', 'overall_score', 'final_grade'
        ]

    # Customizing widgets and labels
    gender = forms.ChoiceField(choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    school_type = forms.ChoiceField(choices=[('public', 'Public'), ('private', 'Private')])
    parent_education = forms.ChoiceField(choices=[
        ('no formal', 'No Formal'),
        ('high school', 'High School'),
        ('diploma', 'Diploma'),
        ('graduate', 'Graduate'),
        ('post graduate', 'Post Graduate'),
        ('phd', 'PhD')
    ])
    internet_access = forms.ChoiceField(choices=[('yes', 'Yes'), ('no', 'No')])
    extra_activities = forms.ChoiceField(choices=[('yes', 'Yes'), ('no', 'No')])
    travel_time = forms.ChoiceField(choices=[
        ('<15 min', '<15 min'),
        ('15-30 min', '15-30 min'),
        ('30-60 min', '30-60 min'),
        ('>60 min', '>60 min')
    ])
    study_method = forms.ChoiceField(choices=[
        ('notes', 'Notes'),
        ('textbook', 'Textbook'),
        ('group study', 'Group Study'),
        ('coaching', 'Coaching'),
        ('online videos', 'Online Videos'),
        ('mixed', 'Mixed')
    ])
    final_grade = forms.ChoiceField(choices=[
        ('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D'), ('e', 'E'), ('f', 'F')
    ])


# Form for Login
class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())


# Form for updating student data
class StudentUpdateForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'student_id', 'name', 'department', 'age', 'study_hours',
            'attendance_percentage', 'math_score', 'science_score',
            'english_score', 'overall_score', 'final_grade'
        ]


class StudentBulkUploadForm(forms.Form):
    file = forms.FileField(
        label="Select CSV or Excel File",
        help_text="Upload a file with columns matching the student data requirements."
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        help_text="Optional: Override department for all students in this file."
    )


class InterventionForm(forms.ModelForm):
    class Meta:
        model = Intervention
        fields = ['intervention_type', 'status', 'action_taken']
        widgets = {
            'action_taken': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe the specific actions or recommendations...'}),
        }