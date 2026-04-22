from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='root'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Unified Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin/dashboard/', views.dashboard, name='admin_dashboard'),
    path('hod/dashboard/', views.dashboard, name='hod_dashboard'),

    # Admin Management
    path('staff/', views.staff_list, name='staff_list'),
    path('hods/', views.hod_list, name='hod_list'),  # Legacy redirect
    path('departments/', views.department_list, name='department_list'),
    path('interventions/', views.intervention_list, name='intervention_list'),
    path('hod/interventions/', views.intervention_list, name='hod_intervention_list'), # Legacy support
    path('ads/staff/delete/<int:user_id>/', views.delete_staff, name='delete_staff'),
    path('ads/staff/update/<int:user_id>/', views.update_staff, name='ads_staff_update'),
    path('staff/profile/', views.staff_profile, name='staff_profile'),
    
    # Student Management
    path('students/', views.student_list, name='student_list'),
    path('ads/student/bulk-upload/', views.bulk_upload_students, name='bulk_upload_students'),
    
    # Update & Delete
    path('ads/student/update/<str:student_id>/', views.admin_update_student, name='ads_student_update'),
    path('ads/department/update/<int:dept_id>/', views.admin_update_department, name='ads_department_update'),
    
    path('ads/student/delete/<str:student_id>/', views.delete_student, name='delete_student'),
    path('ads/department/delete/<int:dept_id>/', views.delete_department, name='delete_department'),
    
    # HOD Specific Pages
    path('hod/students/', views.hod_student_list, name='hod_student_list'),
    path('intervention/record/<str:student_id>/', views.record_intervention, name='record_intervention'),
    path('intervention/update-status/<int:intervention_id>/', views.update_intervention_status, name='update_intervention_status'),
    path('intervention/delete/<int:intervention_id>/', views.delete_intervention, name='delete_intervention'),

    # Reports & Predictions
    path('student/<str:student_id>/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('generate_report/<str:student_id>/', views.generate_report, name='generate_report'),
    path('generate_admin_report/<int:admin_id>/', views.admin_report, name='generate_admin_report'),
    path('generate_hod_report/<int:hod_id>/', views.generate_hod_report, name='generate_hod_report'),
    path('predict/<str:student_id>/', views.predict_student_result, name='predict_student_result'),
    path('bulk-predict/', views.bulk_predict_students, name='bulk_predict_students'),
]
