from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 🔌 ตั้งค่า API Router สำหรับ DRF (พนักงานและงาน)
router = DefaultRouter()
router.register(r'employees', views.EmployeeViewSet, basename='api-employee')
router.register(r'tasks', views.TaskViewSet, basename='api-task')

urlpatterns = [
    # 🔐 ระบบบัญชีผู้ใช้ (ย้ายมาจาก userapp)
    path('login/', views.login_view, name='login'),       # หน้าเข้าสู่ระบบ
    path('register/', views.register, name='register'),   # หน้าสมัครสมาชิก
    path('logout/', views.logout_view, name='logout'),    # ออกจากระบบ

    # 🏠 ระบบหลักและจัดการพนักงาน
    path('', views.index, name='index'),
    path('employee/', views.employee, name='employee'),
    path('edit/<int:emp_id>/', views.edit, name='edit'),
    path('delete/<int:emp_id>/', views.delete, name='delete'),
    
    # 📋 ระบบจัดการงาน (Tasks)
    path('assign-task/<int:emp_id>/', views.assign_task, name='assign_task'),
    path('update-task-status/<int:task_id>/', views.update_task_status, name='update_task_status'),
    path('delete-task/<int:task_id>/', views.delete_task, name='delete_task'),
    
    # 📍 ระบบลงเวลาเข้า-ออกงาน (Attendance)
    path('attendance/', views.attendance_page, name='attendance_page'),
    path('attendance/report/', views.attendance_report, name='attendance_report'),
    
    # ✈️ ระบบจัดการใบลา (Leave)
    path('leave/request/', views.request_leave, name='request_leave'),
    path('leave/approvals/', views.leave_approval_list, name='leave_approval_list'),
    path('leave/update/<int:leave_id>/<str:action>/', views.update_leave_status, name='update_leave_status'),
    
    # 👤 ระบบโปรไฟล์ (Profile) ของใหม่ที่เพิ่งเพิ่ม
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    
    # 🌐 ระบบ API Endpoint
    path('api/', include(router.urls)),
    path('api/attendance/record/', views.record_attendance, name='record_attendance'),
]