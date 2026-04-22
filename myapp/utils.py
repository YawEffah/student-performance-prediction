from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


def send_intervention_email(student, manager, intervention_type):
    """
    Sends a rich HTML email alert to relevant stakeholders when an intervention is recorded.
    """
    subject = f'Intervention Recorded: {student.name}'
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    
    context = {
        'manager_name': manager.name or manager.email,
        'student_name': student.name,
        'student_id': student.student_id,
        'intervention_type': intervention_type,
        'department_name': student.department.name if student.department else 'N/A',
        'dashboard_url': f"{site_url}/student/{student.student_id}/dashboard/",
    }

    html_body = render_to_string('emails/intervention_alert_email.html', context)
    plain_body = (
        f"Hello {manager.name or manager.email},\n\n"
        f"A new intervention '{intervention_type}' has been recorded for {student.name}.\n"
        f"View details: {site_url}/student/{student.student_id}/dashboard/\n\n"
        f"EduPredict Academic Support Team"
    )

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=plain_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[manager.email],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)
        return True
    except Exception as e:
        print(f"Error sending intervention email: {e}")
        return False


def send_risk_alert_email(student):
    """
    Sends a rich HTML email alert to every HOD in the student's department
    when the student is classified as High Risk.
    Uses the unified User model — filters staff by department and user_type.
    """
    from .models import User

    if not student.department:
        return False

    hods = User.objects.filter(user_type='hod', department=student.department)
    if not hods.exists():
        return False

    subject = f'⚠ At-Risk Alert: {student.name} — {student.department.name}'

    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')

    for hod in hods:
        context = {
            'hod_name': hod.name or hod.email,
            'student_name': student.name,
            'student_id': student.student_id,
            'department_name': student.department.name,
            'overall_score': student.overall_score or 'N/A',
            'attendance': student.attendance_percentage or 'N/A',
            'study_hours': student.study_hours or 'N/A',
            'final_grade': student.final_grade or 'N/A',
            'dashboard_url': f"{site_url}/student/{student.student_id}/dashboard/",
        }

        html_body = render_to_string('emails/risk_alert_email.html', context)
        plain_body = (
            f"Hello {hod.name or hod.email},\n\n"
            f"CRITICAL ALERT: {student.name} (ID: {student.student_id}) has been flagged as HIGH RISK.\n\n"
            f"Department : {student.department.name}\n"
            f"Score      : {student.overall_score}%\n"
            f"Attendance : {student.attendance_percentage}%\n\n"
            f"Login to review: {site_url}/student/{student.student_id}/dashboard/\n\n"
            f"EduPredict Academic Monitoring System"
        )

        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=plain_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[hod.email],
            )
            msg.attach_alternative(html_body, "text/html")
            msg.send(fail_silently=False)
        except Exception as e:
            print(f"Error sending risk alert to {hod.email}: {e}")

    return True
