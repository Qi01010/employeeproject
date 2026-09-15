from django.contrib import admin
from .models import Employee, Task, Attendance, LeaveRequest

# ลงทะเบียนโมเดลทั้งหมดเพื่อให้แสดงและจัดการได้ในระบบ Django Admin
admin.site.register(Employee)
admin.site.register(Task)
admin.site.register(Attendance)
admin.site.register(LeaveRequest)