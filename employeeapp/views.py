from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone

from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Employee, Task, Attendance, LeaveRequest, Profile, Equipment, EquipmentBorrow
from .serializers import EmployeeSerializer, TaskSerializer
from .forms import EmployeeForm, LeaveForm, ProfileForm

def is_admin(user):
    return user.is_superuser or user.is_staff

# ================= 🔐 ระบบบัญชี =================
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            messages.error(request, 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')


# ================= 👤 ระบบโปรไฟล์ =================
@login_required(login_url='login')
def profile(request):
    user_profile, created = Profile.objects.get_or_create(user=request.user)
    return render(request, 'profile.html', {'profile': user_profile})

@login_required(login_url='login')
def profile_edit(request):
    user = request.user
    user_profile, created = Profile.objects.get_or_create(user=user)
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        form = ProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=user_profile)
    return render(request, 'profile_edit.html', {'form': form, 'profile': user_profile})


# ================= 🏠 ระบบหน้าหลัก และ ทำเนียบพนักงาน =================
@login_required(login_url='login')
def index(request):
    search_query = request.GET.get('search', '')
    if search_query:
        employee_list = Employee.objects.filter(
            Q(fname__icontains=search_query) |
            Q(lname__icontains=search_query) |
            Q(department__icontains=search_query) |
            Q(address__icontains=search_query)
        ).order_by('-id')
    else:
        employee_list = Employee.objects.all().order_by('-id')
    
    paginator = Paginator(employee_list, 4)
    page_number = request.GET.get('page', 1)
    employees = paginator.get_page(page_number)

    today = timezone.localdate()
    for emp in employees:
        emp.today_attendance = Attendance.objects.filter(employee=emp, date=today).first()

    return render(request, 'index.html', {'employees': employees, 'search_query': search_query})

@user_passes_test(is_admin, login_url='login')
def employee(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = EmployeeForm()
    return render(request, 'employee.html', {'form': form})

@user_passes_test(is_admin, login_url='login')
def edit(request, emp_id):
    emp = get_object_or_404(Employee, id=emp_id)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=emp)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = EmployeeForm(instance=emp)
    return render(request, 'edit.html', {'form': form, 'emp': emp})

@user_passes_test(is_admin, login_url='login')
def delete(request, emp_id):
    emp = get_object_or_404(Employee, id=emp_id)
    emp.delete()
    return redirect('index')


# ================= 📊 ระบบ Dashboard สถิติ =================
@user_passes_test(is_admin, login_url='login')
def dashboard(request):
    today = timezone.localdate()
    total_emp = Employee.objects.count()
    present_count = Attendance.objects.filter(date=today, check_in__isnull=False).values('employee').distinct().count()
    leave_count = LeaveRequest.objects.filter(start_date__lte=today, end_date__gte=today, status='approved').count()
    absent_count = total_emp - present_count - leave_count
    if absent_count < 0: 
        absent_count = 0

    context = {
        'total_emp': total_emp,
        'present_count': present_count,
        'leave_count': leave_count,
        'absent_count': absent_count
    }
    return render(request, 'dashboard.html', context)


# ================= 📋 ระบบงาน =================
@user_passes_test(is_admin, login_url='login')
def assign_task(request, emp_id):
    emp = get_object_or_404(Employee, id=emp_id)
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        due_date = request.POST.get('due_date')
        Task.objects.create(employee=emp, title=title, description=description, due_date=due_date)
        return redirect('index')
    return render(request, 'assign_task.html', {'emp': emp})

@login_required(login_url='login')
def update_task_status(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['pending', 'in_progress', 'completed']:
            task.status = new_status
            task.save()
    return redirect('index')

@user_passes_test(is_admin, login_url='login')
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.delete()
    return redirect('index')


# ================= 📍 ระบบลงเวลาและใบลา =================
@login_required(login_url='login')
def attendance_page(request):
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        employee = None
    return render(request, 'attendance.html', {'employee': employee})

@user_passes_test(is_admin, login_url='login')
def attendance_report(request):
    today = timezone.localdate()
    employees = Employee.objects.all()
    
    # ดึงข้อมูลการลงเวลาของวันนี้มาผูกกับพนักงานแต่ละคนโดยตรงเพื่อความเสถียร
    for emp in employees:
        emp.today_att = Attendance.objects.filter(employee=emp, date=today).first()

    return render(request, 'attendance_report.html', {'employees': employees, 'today': today})

def request_leave(request):
    if request.method == 'POST':
        form = LeaveForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = LeaveForm()
    return render(request, 'leave_form.html', {'form': form})

@user_passes_test(is_admin, login_url='login')
def leave_approval_list(request):
    leaves = LeaveRequest.objects.all().order_by('-created_at')
    return render(request, 'leave_approval.html', {'leaves': leaves})

@user_passes_test(is_admin, login_url='login')
def update_leave_status(request, leave_id, action):
    leave_obj = get_object_or_404(LeaveRequest, id=leave_id)
    if action == 'approve':
        leave_obj.status = 'approved'
    elif action == 'reject':
        leave_obj.status = 'rejected'
    leave_obj.save()
    return redirect('leave_approval_list')


# ================= 💻 ระบบยืม-คืนอุปกรณ์ =================
@login_required(login_url='login')
def equipment_list(request):
    equipments = Equipment.objects.all()
    borrows = EquipmentBorrow.objects.all().order_by('-id')
    return render(request, 'equipment_list.html', {'equipments': equipments, 'borrows': borrows})

@login_required(login_url='login')
def borrow_equipment(request, eq_id):
    equipment = get_object_or_404(Equipment, id=eq_id)
    if equipment.status != 'available':
        messages.error(request, 'อุปกรณ์นี้ไม่พร้อมใช้งาน')
        return redirect('equipment_list')
    
    try:
        employee_obj = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, 'บัญชีของคุณยังไม่ได้ผูกกับข้อมูลพนักงาน')
        return redirect('equipment_list')

    if request.method == 'POST':
        EquipmentBorrow.objects.create(equipment=equipment, employee=employee_obj, status='borrowing')
        equipment.status = 'borrowed'
        equipment.save()
        messages.success(request, 'ยืมอุปกรณ์สำเร็จ!')
        return redirect('equipment_list')
        
    return render(request, 'borrow_form.html', {'equipment': equipment})

@user_passes_test(is_admin, login_url='login')
def return_equipment(request, borrow_id):
    borrow_obj = get_object_or_404(EquipmentBorrow, id=borrow_id)
    if borrow_obj.status == 'borrowing':
        borrow_obj.status = 'returned'
        borrow_obj.return_date = timezone.localdate()
        borrow_obj.save()
        
        eq = borrow_obj.equipment
        eq.status = 'available'
        eq.save()
        messages.success(request, 'รับคืนอุปกรณ์เรียบร้อยแล้ว')
    return redirect('equipment_list')


# ================= 💵 ระบบคำนวณเงินเดือน (Payroll) =================
@user_passes_test(is_admin, login_url='login')
def payroll_report(request):
    employees = Employee.objects.all()
    payroll_data = []
    
    today = timezone.localdate()
    current_month = today.month
    current_year = today.year

    for emp in employees:
        worked_days = Attendance.objects.filter(
            employee=emp, 
            date__year=current_year, 
            date__month=current_month,
            check_in__isnull=False
        ).count()
        
        monthly_salary = float(emp.salary or 0)
        daily_rate = monthly_salary / 30 if monthly_salary > 0 else 0
        total_pay = worked_days * daily_rate

        payroll_data.append({
            'employee': emp,
            'worked_days': worked_days,
            'monthly_salary': monthly_salary,
            'daily_rate': round(daily_rate, 2),
            'total_pay': round(total_pay, 2),
            'month': current_month,
            'year': current_year
        })

    return render(request, 'payroll_report.html', {'payroll_data': payroll_data, 'current_month': current_month})


# ================= 🌐 ระบบ API =================
class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

@api_view(['POST'])
def record_attendance(request):
    user = request.user
    if not user.is_authenticated:
        return Response({'error': 'กรุณาเข้าสู่ระบบ'}, status=status.HTTP_401_UNAUTHORIZED)
        
    try:
        employee_obj = Employee.objects.get(user=user)
    except Employee.DoesNotExist:
        return Response({'error': 'บัญชีนี้ยังไม่ได้เชื่อมโยงกับรายชื่อพนักงาน'}, status=status.HTTP_404_NOT_FOUND)

    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')
    att_type = request.data.get('type')

    today = timezone.localdate()
    if att_type == 'in':
        attendance, created = Attendance.objects.get_or_create(
            employee=employee_obj, date=today,
            defaults={'check_in': timezone.now(), 'latitude': latitude, 'longitude': longitude, 'status': 'On Time'}
        )
        if not created and attendance.check_in:
            return Response({'error': 'คุณ Check-in ไปแล้ว'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'Check-in สำเร็จ!'}, status=status.HTTP_200_OK)

    elif att_type == 'out':
        attendance = Attendance.objects.filter(employee=employee_obj, date=today).first()
        if not attendance or not attendance.check_in:
            return Response({'error': 'ยังไม่ได้ Check-in'}, status=status.HTTP_400_BAD_REQUEST)
        if attendance.check_out:
            return Response({'error': 'Check-out ไปแล้ว'}, status=status.HTTP_400_BAD_REQUEST)
        
        attendance.check_out = timezone.now()
        attendance.save()
        return Response({'message': 'Check-out สำเร็จ!'}, status=status.HTTP_200_OK)

    return Response({'error': 'ประเภทไม่ถูกต้อง'}, status=status.HTTP_400_BAD_REQUEST)