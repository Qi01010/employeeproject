from django.contrib import admin
from .models import Employee, Task, Attendance, LeaveRequest, Profile, Equipment, EquipmentBorrow

# ลงทะเบียนโมเดลเพื่อให้แสดงในหน้า Admin
admin.site.register(Employee)
admin.site.register(Task)
admin.site.register(Attendance)
admin.site.register(LeaveRequest)
admin.site.register(Profile)
admin.site.register(Equipment)
admin.site.register(EquipmentBorrow)