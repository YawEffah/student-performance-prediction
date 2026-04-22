import os
import pandas as pd
import json
import pickle
import io
import base64
import qrcode
import numpy as np
from datetime import date, datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import HttpResponse, JsonResponse, Http404
from django.db.models import Q, Avg, Count
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from xhtml2pdf import pisa
import matplotlib.pyplot as plt
from io import BytesIO

from .models import User, Student, Department, Intervention
from .forms import LoginForm, StudentForm, StudentUpdateForm, UserForm, DepartmentForm, StudentBulkUploadForm, InterventionForm, StaffRegistrationForm, StaffProfileUpdateForm, StaffUpdateForm
from .utils import send_intervention_email, send_risk_alert_email

from django.contrib.auth import authenticate, login, logout, update_session_auth_hash

@login_required
def staff_profile(request):
    user = request.user
    if request.method == 'POST':
        form = StaffProfileUpdateForm(request.POST, instance=user)
        if user.user_type == 'hod':
            form.fields['department'].disabled = True
            
        if form.is_valid():
            user = form.save()
            # Keep the user logged in after password change
            if form.cleaned_data.get('new_password'):
                update_session_auth_hash(request, user)
            messages.success(request, "Profile and security settings updated successfully.")
            return redirect('staff_profile')
    else:
        form = StaffProfileUpdateForm(instance=user)
        if user.user_type == 'hod':
            form.fields['department'].disabled = True
    
    return render(request, 'staff_profile.html', {'form': form})

# Global cache for model and meta to optimize bulk operations
_cached_model = None
_cached_meta = None

def load_model_and_meta():
    """
    Helper function to load the model and metadata with simple global caching.
    """
    global _cached_model, _cached_meta
    
    if _cached_model is not None and _cached_meta is not None:
        return _cached_model, _cached_meta
        
    model_path = os.path.join(settings.BASE_DIR, 'random_forest_model.pkl')
    meta_path = os.path.join(settings.BASE_DIR, 'model_metadata.json')
    
    with open(model_path, 'rb') as file:
        _cached_model = pickle.load(file)
    with open(meta_path, 'r') as file:
        _cached_meta = json.load(file)
        
    return _cached_model, _cached_meta

def perform_student_prediction(student):
    """
    Helper function to perform prediction and save results to the database.
    """
    try:
        model, meta = load_model_and_meta()
        features = student.get_ml_features(meta)
        prediction = model.predict([features])
        prediction_value = int(prediction[0])

        student.result = prediction_value
        student.risk_level = 'High' if prediction_value == 0 else 'Low'
        student.last_prediction_date = timezone.now()
        student.save()

        # Trigger email alert if student is high risk
        if student.risk_level == 'High':
            send_risk_alert_email(student)
            
        return True, prediction_value
    except Exception as e:
        return False, str(e)

# Helper to generate QR code
def generate_qr_code(data):
    qr = qrcode.make(data)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    return f'data:image/png;base64,{qr_base64}'

# Helper to generate Pie Chart
def generate_pie_chart(students_result_0, students_result_1, students_result_other):
    labels = ["At Risk", "Low Risk", "Pending"]
    sizes = [students_result_0.count(), students_result_1.count(), students_result_other.count()]
    colors = ["#ef4444", "#10b981", "#4f46e5"]

    plt.figure(figsize=(4, 4))
    plt.pie(sizes, labels=labels, autopct="%1.1f%%", colors=colors, startangle=90)
    plt.axis("equal")

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    buffer.close() # Close figure to free memory
    plt.close()
    
    return base64.b64encode(buffer.getvalue()).decode()

# Login view
def login_view(request):
    if request.user.is_authenticated:
            return redirect('dashboard')

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid email or password')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

# Student Dashboard View
@login_required
def student_dashboard(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)
    
    # Students no longer login; only Admins and HODs can view dashboards
    if request.user.user_type not in ['admin', 'hod']:
        raise Http404("Unauthorized access.")

    dept_students = Student.objects.filter(department=student.department)

    mean_attendance = dept_students.aggregate(Avg('attendance_percentage'))['attendance_percentage__avg']
    mean_study_hours = dept_students.aggregate(Avg('study_hours'))['study_hours__avg']
    mean_score = dept_students.aggregate(Avg('overall_score'))['overall_score__avg']

    chart_data = {
        'labels': ['Attendance', 'Study Hours', 'Score'],
        'student_data': [student.attendance_percentage or 0, student.study_hours or 0, student.overall_score or 0],
        'avg_data': [mean_attendance or 0, mean_study_hours or 0, mean_score or 0]
    }

    return render(request, 'student_dashboard.html', {
        'student': student,
        'mean_attendance': mean_attendance,
        'mean_study_hours': mean_study_hours,
        'mean_score': mean_score,
        'chart_data_json': json.dumps(chart_data)
    })

@login_required
def dashboard(request):
    user_type = request.user.user_type
    context = {'user_type': user_type}
    
    if user_type == 'admin':
        students = Student.objects.all()
        total_staff = User.objects.filter(user_type__in=['hod', 'admin']).count()
        departments = Department.objects.all()
        interventions = Intervention.objects.all().order_by('-created_at')
        
        # Comparative Departmental Data
        dept_labels = []
        dept_risk_data = []
        dept_low_data = []
        for dept in departments:
            dept_labels.append(dept.name)
            dept_students = students.filter(department=dept)
            dept_risk_data.append(dept_students.filter(result=0).count())
            dept_low_data.append(dept_students.filter(result=1).count())

        context.update({
            'total_students': students.count(),
            'total_hods': total_staff,
            'total_departments': departments.count(),
            'students_with_zero_result': students.filter(result=0),
            'interventions': interventions,
            'chart_data_json': json.dumps({
                'type': 'bar',
                'labels': dept_labels,
                'risk_data': dept_risk_data,
                'low_data': dept_low_data
            }),
        })

    elif user_type == 'hod':
        students = Student.objects.filter(department=request.user.department)
        interventions = Intervention.objects.filter(student__department=request.user.department).order_by('-created_at')
        students_at_risk = students.filter(result=0).order_by('name')
        
        # Radar Chart Data: Factor Comparison
        at_risk_metrics = students.filter(result=0).aggregate(
            avg_attendance=Avg('attendance_percentage'),
            avg_score=Avg('overall_score'),
            avg_study=Avg('study_hours')
        )
        low_risk_metrics = students.filter(result=1).aggregate(
            avg_attendance=Avg('attendance_percentage'),
            avg_score=Avg('overall_score'),
            avg_study=Avg('study_hours')
        )

        # Intervention Distribution (Type & Status)
        intervention_types = dict(Intervention.INTERVENTION_TYPES)
        type_counts = interventions.values('intervention_type').annotate(count=Count('intervention_type'))
        status_counts = interventions.values('status').annotate(count=Count('status'))

        type_data = {t: 0 for t in intervention_types.keys()}
        for entry in type_counts:
            type_data[entry['intervention_type']] = entry['count']
            
        status_data = {s[0]: 0 for s in Intervention.STATUS_CHOICES}
        for entry in status_counts:
            status_data[entry['status']] = entry['count']

        # Bubble Chart Data: Individual Student Clusters
        bubble_data = []
        for s in students:
            bubble_data.append({
                'x': float(s.attendance_percentage or 0),
                'y': float(s.overall_score or 0),
                'r': float(s.study_hours or 0) * 1.5, # Weight radius for visibility
                'name': s.name,
                'id': s.student_id,
                'is_risk': s.result == 0 or s.result == '0'
            })

        context.update({
            'hod': request.user,
            'students': students,
            'students_zero': students_at_risk.count(),
            'students_at_risk': students_at_risk,
            'interventions': interventions,
            'chart_data_json': json.dumps({
                'type': 'bubble',
                'dataset': bubble_data
            }),
            'support_chart_json': json.dumps({
                'types': {
                    'labels': [intervention_types[k] for k in type_data.keys()],
                    'values': list(type_data.values())
                },
                'status': {
                    'labels': list(status_data.keys()),
                    'values': list(status_data.values())
                }
            })
        })
    
    return render(request, 'dashboard.html', context)


@login_required
def hod_student_list(request):
    return redirect('student_list')

@login_required
def intervention_list(request):
    if request.user.user_type == 'admin':
        interventions = Intervention.objects.all().order_by('-created_at')
    else:
        # HODs see interventions for their department
        interventions = Intervention.objects.filter(student__department=request.user.department).order_by('-created_at')
        
    return render(request, 'intervention_list.html', {'interventions': interventions})


@login_required
def department_list(request):
    if request.method == "POST":
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Department established successfully.")
            return redirect('department_list')
    else:
        form = DepartmentForm()
    departments = Department.objects.all()
    return render(request, 'department_list.html', {'departments': departments, 'form': form})


@login_required
def staff_list(request):
    if request.user.user_type != 'admin':
        messages.error(request, "Unauthorized access.")
        return redirect('dashboard')
        
    if request.method == "POST":
        user_type = request.POST.get('user_type')
        user_form = UserForm(request.POST)
        profile_form = StaffRegistrationForm(request.POST)
            
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.user_type = user_type
            # Merge profile fields into user
            for field in profile_form.cleaned_data:
                setattr(user, field, profile_form.cleaned_data[field])
            user.save()
            
            messages.success(request, f"{user_type.upper()} {user.name} registered successfully.")
            return redirect('staff_list')
    else:
        user_form = UserForm()
        profile_form = StaffRegistrationForm()
        
    # Unified staff list
    staff = User.objects.filter(user_type__in=['hod', 'admin']).select_related('department').order_by('user_type', 'name')
    
    return render(request, 'staff_list.html', {
        'staff_members': staff,
        'user_form': user_form,
        'profile_form': profile_form,
    })

@login_required
def delete_staff(request, user_id):
    if request.user.user_type != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    user = get_object_or_404(User, id=user_id)
    # Prevent self-deletion
    if user == request.user:
        return JsonResponse({'error': 'You cannot delete your own account.'}, status=400)
        
    user.delete()
    return JsonResponse({'message': 'Staff member removed successfully.'})

@login_required
def record_intervention(request, student_id):
    if request.user.user_type not in ['hod', 'admin']:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    student = get_object_or_404(Student, student_id=student_id)
    
    if request.method == 'POST':
        form = InterventionForm(request.POST)
        if form.is_valid():
            intervention = form.save(commit=False)
            intervention.student = student
            intervention.manager = request.user
            intervention.save()
            
            # Send automated email alert
            send_intervention_email(student, request.user, intervention.intervention_type)
            
            return JsonResponse({'message': 'Intervention recorded successfully.'})
        return JsonResponse({'error': 'Invalid form data.'}, status=400)
    
    return JsonResponse({'error': 'Invalid request method.'}, status=405)

@login_required
def update_intervention_status(request, intervention_id):
    intervention = get_object_or_404(Intervention, id=intervention_id)
    
    # Permission: Admin can update anything, HOD can update anything in their department
    is_admin = request.user.user_type == 'admin'
    is_dept_hod = request.user.user_type == 'hod' and intervention.student.department == request.user.department
    
    if not is_admin and not is_dept_hod:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Intervention.STATUS_CHOICES):
            intervention.status = new_status
            intervention.save()
            return JsonResponse({'message': f'Status updated to {new_status}.'})
        return JsonResponse({'error': 'Invalid status.'}, status=400)
        
    return JsonResponse({'error': 'Invalid request method.'}, status=405)

@login_required
def delete_intervention(request, intervention_id):
    intervention = get_object_or_404(Intervention, id=intervention_id)
    
    # Permission: Admin can delete anything, HOD can delete anything in their department
    is_admin = request.user.user_type == 'admin'
    is_dept_hod = request.user.user_type == 'hod' and intervention.student.department == request.user.department
    
    if not is_admin and not is_dept_hod:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    intervention.delete()
    return JsonResponse({'message': 'Intervention deleted successfully.'})


# Prediction logic
@login_required
def predict_student_result(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)
    success, result = perform_student_prediction(student)
    
    if success:
        return JsonResponse({'student_id': student_id, 'prediction': result, 'risk': student.risk_level})
    else:
        return JsonResponse({'error': result}, status=500)

@login_required
def bulk_predict_students(request):
    """
    Triggers prediction for all students visible to the current user (Admin: All, HOD: Department only).
    """
    if request.user.user_type == 'admin':
        students = Student.objects.all()
    else:
        students = Student.objects.filter(department=request.user.department)
    
    success_count = 0
    error_count = 0
    for student in students:
        try:
            success, _ = perform_student_prediction(student)
            if success:
                success_count += 1
            else:
                error_count += 1
        except Exception as e:
            error_count += 1
            print(f"Error predicting for {student.student_id}: {e}")
            
    return JsonResponse({
        'message': f'Processed {success_count + error_count} students. Success: {success_count}, Errors: {error_count}',
        'success_count': success_count,
        'error_count': error_count
    })

# Reports
def generate_report(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)
    message_content = "No recommendations available."

    # Find the HOD for this student's department
    dept_hod = User.objects.filter(user_type='hod', department=student.department).first()

    form_data = {
        "name": student.name,
        "student_id": student.student_id,
        "hod": dept_hod.name if dept_hod else "Not Assigned",
        "dept_name": student.department.name if student.department else "Not Assigned",
        "age": student.age,
        "gender": student.get_gender_display(),
        "parent_education": student.get_parent_education_display(),
        "school_type": student.get_school_type_display(),
        "study_hours": student.study_hours,
        "attendance_percentage": student.attendance_percentage,
        "internet_access": student.internet_access,
        "travel_time": student.travel_time,
        "extra_activities": student.extra_activities,
        "study_method": student.get_study_method_display(),
        "math_score": student.math_score,
        "science_score": student.science_score,
        "english_score": student.english_score,
        "overall_score": student.overall_score,
        "final_grade": student.final_grade,
        "risk_level": student.risk_level,
        "messages": message_content,
    }

    html_string = render_to_string('student_report_template.html', form_data)
    pdf_file = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.StringIO(html_string), dest=pdf_file)
    
    if pisa_status.err:
        return HttpResponse("Error generating PDF", content_type="text/plain")

    pdf_file.seek(0)
    response = HttpResponse(pdf_file.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="student_report_{student_id}.pdf"'
    return response

def generate_hod_report(request, hod_id):
    hod_user = get_object_or_404(User, id=hod_id, user_type='hod')
    students = Student.objects.filter(department=hod_user.department)
    
    students_result_0 = students.filter(result=0)
    students_result_1 = students.filter(result=1)
    students_result_other = students.exclude(result__in=[0, 1])

    form_data = {
        "name": hod_user.name,
        "phone": hod_user.phone,
        "address": hod_user.address,
        "subject": hod_user.department.name if hod_user.department else "N/A",
        "classes": hod_user.department.name if hod_user.department else "N/A",
        "students_result_0": students_result_0,
        "students_result_1": students_result_1,
        "students_result_other": students_result_other,
        "qr": generate_qr_code(f"HOD: {hod_user.name} ID: {hod_user.id}"),
        "report_date": date.today().strftime("%Y-%m-%d"),
        "logo": os.path.join(settings.BASE_DIR, 'myapp', 'static', 'user.png')
    }
    form_data["pie_chart"] = generate_pie_chart(students_result_0, students_result_1, students_result_other)

    html_string = render_to_string('hod_report_template.html', form_data)
    pdf_file = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.StringIO(html_string), dest=pdf_file)

    if pisa_status.err:
        return HttpResponse("Error generating PDF", content_type="text/plain")

    pdf_file.seek(0)
    response = HttpResponse(pdf_file.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="hod_report_{hod_id}.pdf"'
    return response

def admin_report(request, admin_id):
    admin_user = get_object_or_404(User, id=admin_id, user_type='admin')
    total_staff = User.objects.filter(user_type__in=['hod', 'admin']).count()
    total_students = Student.objects.count()
    total_departments = Department.objects.count()
    
    total_students_result_0 = Student.objects.filter(result=0).count()
    total_students_result_1 = Student.objects.filter(result=1).count()

    context = {
        'admin': admin_user,
        'total_hods': total_staff,
        'total_students': total_students,
        'total_departments': total_departments,
        'total_students_result_0': total_students_result_0,
        'total_students_result_1': total_students_result_1,
        'report_date': date.today().strftime("%Y-%m-%d"),
        'qr': generate_qr_code(f"Admin Report: {admin_ } - {date.today()}"),
        'logo': os.path.join(settings.BASE_DIR, 'myapp', 'static', 'user.png')
    }

    html_string = render_to_string('ads_report_template.html', context)
    pdf_file = BytesIO()
    pisa_status = pisa.CreatePDF(html_string, dest=pdf_file)

    if pisa_status.err:
        return HttpResponse("Error generating PDF", content_type="text/plain")

    pdf_file.seek(0)
    response = HttpResponse(pdf_file.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="admin_report_{admin_id}.pdf"'
    return response


# CRUD
@login_required
def create_student(request):
    if request.method == "POST":
        student_form = StudentForm(request.POST)
        if student_form.is_valid():
            student = student_form.save()
            perform_student_prediction(student)
            return redirect('student_list')
    else:
        student_form = StudentForm()
    return render(request, 'create_student.html', {'student_form': student_form})

def create_department(request):
    if request.method == "POST":
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    else:
        form = DepartmentForm()
    return render(request, 'create_department.html', {'form': form})

@login_required
def student_list(request):
    if request.method == "POST":
        student_form = StudentForm(request.POST)
        if student_form.is_valid():
            student = student_form.save(commit=False)
            # Force HODs to their own department
            if request.user.user_type == 'hod':
                student.department = request.user.department
            student.save()
            perform_student_prediction(student)
            messages.success(request, f"Student {student.name} enrolled successfully.")
            return redirect('student_list')
    else:
        # Pre-fill department for HODs in the form
        initial_data = {}
        if request.user.user_type == 'hod':
            initial_data['department'] = request.user.department
        student_form = StudentForm(initial=initial_data)
    
    # Base query based on role
    if request.user.user_type == 'admin':
        students_query = Student.objects.all()
    else:
        students_query = Student.objects.filter(department=request.user.department)
        
    # Search and Filtering
    q = request.GET.get('q')
    risk_level = request.GET.get('risk_level')
    
    if q:
        students_query = students_query.filter(
            Q(name__icontains=q) | Q(student_id__icontains=q)
        )
    
    if risk_level == 'High':
        students_query = students_query.filter(result=0)
    elif risk_level == 'Low':
        students_query = students_query.filter(result=1)
    elif risk_level == 'Pending':
        students_query = students_query.exclude(result__in=[0, 1])

    students_query = students_query.order_by('name')

    # Pagination
    paginator = Paginator(students_query, 10) # 10 students per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'students_list.html', {
        'students': page_obj, 
        'student_form': student_form,
        'current_risk_level': risk_level,
        'search_query': q
    })

# Legacy hod_list now redirects to staff_list
def hod_list(request):
    return redirect('staff_list')


@login_required
def update_staff(request, user_id):
    """Edit an existing staff member's profile and credentials."""
    if request.user.user_type != 'admin':
        messages.error(request, "Unauthorized access.")
        return redirect('dashboard')

    staff_member = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        form = StaffUpdateForm(request.POST, instance=staff_member)
        if form.is_valid():
            form.save()
            messages.success(request, f"{staff_member.name or staff_member.email} updated successfully.")
            return redirect('staff_list')
    else:
        form = StaffUpdateForm(instance=staff_member)

    return render(request, 'ads_staff_update.html', {'form': form, 'staff_member': staff_member})

@login_required
def admin_update_student(request, student_id):
    if request.user.user_type != 'admin':
        messages.error(request, "Unauthorized access.")
        return redirect('dashboard')
    student = get_object_or_404(Student, student_id=student_id)
    if request.method == 'POST':
        form = StudentUpdateForm(request.POST, instance=student)
        if form.is_valid():
            student = form.save()
            perform_student_prediction(student)
            return redirect('student_list')
    else:
        form = StudentUpdateForm(instance=student)
    return render(request, 'ads_student_update.html', {'form': form})

@login_required
def admin_update_department(request, dept_id):
    if request.user.user_type != 'admin':
        messages.error(request, "Unauthorized access.")
        return redirect('dashboard')
    dept = get_object_or_404(Department, id=dept_id)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=dept)
        if form.is_valid():
            form.save()
            return redirect('department_list')
    else:
        form = DepartmentForm(instance=dept)
    return render(request, 'ads_department_update.html', {'form': form})

@login_required
def delete_student(request, student_id):
    if request.user.user_type != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    student = get_object_or_404(Student, student_id=student_id)
    student.delete()
    return JsonResponse({"message": "Student deleted successfully."})

@login_required
def delete_department(request, dept_id):
    if request.user.user_type != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    dept = get_object_or_404(Department, id=dept_id)
    dept.delete()
    return JsonResponse({"message": "Department deleted successfully."})

@login_required
def bulk_upload_students(request):
    if request.user.user_type not in ['admin', 'hod']:
        messages.error(request, "Unauthorized access.")
        return redirect('login')

    is_hod = request.user.user_type == 'hod'

    if request.method == 'POST':
        form = StudentBulkUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            # Admins can override, HODs are locked to their department
            dept_override = request.user.department if is_hod else form.cleaned_data.get('department')
            
            try:
                # To preserve leading zeros in student_id, we need to read it as a string
                # We'll read the first few rows to find the student_id column name (case-insensitive)
                temp_df = pd.read_csv(file, nrows=0) if file.name.endswith('.csv') else pd.read_excel(file, nrows=0)
                original_cols = temp_df.columns.tolist()
                id_col = next((c for c in original_cols if c.lower().replace(' ', '_') == 'student_id'), None)
                
                dtype_map = {id_col: str} if id_col else {}
                
                # RESET file pointer before reading again
                file.seek(0)
                
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file, dtype=dtype_map)
                else:
                    df = pd.read_excel(file, dtype=dtype_map)
                
                # Standardizing columns
                df.columns = [c.lower().replace(' ', '_') for c in df.columns]
                
                required_cols = ['name', 'student_id']
                missing = [c for c in required_cols if c not in df.columns]
                if missing:
                    messages.error(request, f"Missing required columns: {', '.join(missing)}")
                    return render(request, 'bulk_upload_students.html', {'form': form})

                success_count = 0
                error_count = 0
                
                for _, row in df.iterrows():
                    try:
                        # Clean student_id: ensure it's a string and strip any accidental '.0'
                        raw_id = str(row['student_id']).strip()
                        if raw_id.endswith('.0'):
                            raw_id = raw_id[:-2]
                            
                        # Find or create department if not overridden (Admins only)
                        dept = dept_override
                        if not is_hod and not dept and 'department' in df.columns:
                            dept_name = str(row['department']).strip()
                            dept, _ = Department.objects.get_or_create(name=dept_name)
                        
                        student, created = Student.objects.update_or_create(
                            student_id=raw_id,
                            defaults={
                                'name': row['name'],
                                'department': dept,
                                'age': row.get('age'),
                                'gender': row.get('gender', 'other').lower(),
                                'school_type': row.get('school_type'),
                                'parent_education': row.get('parent_education'),
                                'study_hours': row.get('study_hours'),
                                'attendance_percentage': row.get('attendance_percentage', row.get('attendance', 100)),
                                'internet_access': row.get('internet_access'),
                                'travel_time': row.get('travel_time'),
                                'extra_activities': row.get('extra_activities'),
                                'study_method': row.get('study_method'),
                                'overall_score': row.get('overall_score', 0),
                                'final_grade': row.get('final_grade'),
                            }
                        )
                        perform_student_prediction(student)
                        success_count += 1
                    except Exception as e:
                        error_count += 1
                        print(f"Error importing row: {e}")

                messages.success(request, f"Successfully imported {success_count} students. Errors: {error_count}")
                return redirect('student_list')
                
            except Exception as e:
                messages.error(request, f"Error processing file: {e}")
    else:
        form = StudentBulkUploadForm()
    
    return render(request, 'bulk_upload_students.html', {'form': form})
