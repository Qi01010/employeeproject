from django.db import migrations, models
from django.db.models import Count


def check_duplicates(apps, schema_editor):
    Attendance = apps.get_model('employeeapp', 'Attendance')
    if Attendance.objects.values('employee_id', 'date').annotate(n=Count('id')).filter(n__gt=1).exists():
        raise RuntimeError('พบรายการลงเวลาซ้ำวัน กรุณาสำรองและตรวจสอบรายการซ้ำก่อน migrate ระบบไม่ได้ลบข้อมูลเดิม')


class Migration(migrations.Migration):
    dependencies = [('employeeapp', '0009_attendancehost')]
    operations = [
        migrations.RunPython(check_duplicates, migrations.RunPython.noop),
        migrations.AddConstraint(model_name='attendance', constraint=models.UniqueConstraint(fields=('employee', 'date'), name='unique_employee_attendance_day')),
    ]
