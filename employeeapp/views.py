import csv
import calendar
from decimal import Decimal, ROUND_HALF_UP
from datetime import timedelta
from django.http import HttpResponse
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.exceptions import PermissionDenied
from .forms import ReportFilterForm, PayrollFilterForm

import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .geofence import (parse_position, distance_meters, ATTENDANCE_RADIUS_METERS,
                       ATTENDANCE_CENTER_LATITUDE, ATTENDANCE_CENTER_LONGITUDE)

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
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
            Q(department__icontains=search_query)
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
@require_POST
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
    return render(request, 'assign_task.html', {'employee': emp})

@login_required(login_url='login')
@require_POST
def update_task_status(request, task_id):
    tasks = Task.objects.all() if is_admin(request.user) else Task.objects.filter(employee__user=request.user)
    task = get_object_or_404(tasks, id=task_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['pending', 'in_progress', 'completed']:
            task.status = new_status
            task.save()
    return redirect('index')

@user_passes_test(is_admin, login_url='login')
@require_POST
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
    return render(request, 'attendance.html', {'employee': employee,
        'attendance_center_latitude': ATTENDANCE_CENTER_LATITUDE,
        'attendance_center_longitude': ATTENDANCE_CENTER_LONGITUDE})

@user_passes_test(is_admin, login_url='login')
def attendance_report(request):
    form = ReportFilterForm(request.GET or {'start': timezone.localdate().isoformat(), 'end': timezone.localdate().isoformat()})
    records = Attendance.objects.none()
    if form.is_valid():
        records = Attendance.objects.select_related('employee').filter(date__range=(form.cleaned_data['start'], form.cleaned_data['end'])).order_by('-date', 'employee_id')
        if form.cleaned_data['employee']:
            records = records.filter(employee=form.cleaned_data['employee'])
        if request.GET.get('export') == 'csv':
            return csv_response('attendance.csv', ['วันที่', 'พนักงาน', 'แผนก', 'เข้า', 'ออก', 'ละติจูด', 'ลองจิจูด'],
                ([x.date, str(x.employee), x.employee.department, local_time(x.check_in), local_time(x.check_out), x.latitude, x.longitude] for x in records))
    elif request.GET.get('export'):
        return HttpResponse('ตัวกรองไม่ถูกต้อง', status=400)
    return render(request, 'attendance_report.html', {'form': form, 'records': records})

@login_required(login_url='login')
def request_leave(request):
    if is_admin(request.user):
        return HttpResponseForbidden('บัญชีแอดมินไม่มีสิทธิ์ยื่นใบลา')

    employee_obj = Employee.objects.filter(user=request.user).first()
    if not employee_obj:
        return HttpResponseForbidden('บัญชียังไม่ได้ผูกกับพนักงาน กรุณาติดต่อแอดมิน')
    form = LeaveForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        leave = form.save(commit=False)
        leave.employee = employee_obj
        leave.status = 'pending'
        leave.save()
        return redirect('index')
    return render(request, 'leave_form.html', {'form': form, 'employee': employee_obj})

@user_passes_test(is_admin, login_url='login')
def leave_approval_list(request):
    leaves = LeaveRequest.objects.all().order_by('-created_at')
    return render(request, 'leave_approval.html', {'leaves': leaves})

@user_passes_test(is_admin, login_url='login')
@require_POST
def update_leave_status(request, leave_id, action):
    if action not in ('approve', 'reject'):
        return HttpResponse('คำสั่งไม่ถูกต้อง', status=400)
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
@require_POST
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
    form = PayrollFilterForm(request.GET or {'month': timezone.localdate().strftime('%Y-%m'), 'mode': 'monthly', 'divisor': '30'})
    rows = []
    if form.is_valid():
        start = form.cleaned_data['month']
        end = start.replace(day=calendar.monthrange(start.year, start.month)[1])
        for emp in Employee.objects.all():
            worked = Attendance.objects.filter(employee=emp, date__range=(start, end), check_in__isnull=False).values('date').distinct().count()
            leave_dates = set()
            for leave in LeaveRequest.objects.filter(employee=emp, status='approved', start_date__lte=end, end_date__gte=start):
                day = max(start, leave.start_date)
                while day <= min(end, leave.end_date):
                    leave_dates.add(day)
                    day += timedelta(days=1)
            base = emp.salary or Decimal('0')
            rate = base / form.cleaned_data['divisor']
            amount = base if form.cleaned_data['mode'] == 'monthly' else rate * worked
            rows.append({'employee': emp, 'worked_days': worked, 'leave_days': len(leave_dates), 'monthly_salary': base,
                         'total_pay': amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)})
        if request.GET.get('export') == 'csv':
            return csv_response('payroll.csv', ['พนักงาน', 'เดือน', 'วิธี', 'จำนวนวันหาร', 'ลงเวลา (วัน)', 'ลาอนุมัติ (วันปฏิทิน)', 'เงินเดือนตั้งต้น', 'ยอดก่อนปรับปรุง'],
                ([str(x['employee']), start.strftime('%Y-%m'), form.cleaned_data['mode'], form.cleaned_data['divisor'], x['worked_days'], x['leave_days'], x['monthly_salary'], x['total_pay']] for x in rows))
    elif request.GET.get('export'):
        return HttpResponse('ตัวกรองไม่ถูกต้อง', status=400)
    return render(request, 'payroll_report.html', {'form': form, 'payroll_data': rows})


# ================= 🌐 ระบบ API =================
class EmployeeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer

class TaskViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TaskSerializer

    def get_queryset(self):
        qs = Task.objects.all()
        return qs if is_admin(self.request.user) else qs.filter(employee__user=self.request.user)

    def perform_create(self, serializer):
        if not is_admin(self.request.user):
            raise PermissionDenied('เฉพาะแอดมินมอบหมายงานได้')
        serializer.save()

    def perform_update(self, serializer):
        if not is_admin(self.request.user) and set(self.request.data) - {'status'}:
            raise PermissionDenied('พนักงานแก้ได้เฉพาะสถานะงานของตนเอง')
        serializer.save()

    def perform_destroy(self, instance):
        if not is_admin(self.request.user):
            raise PermissionDenied('เฉพาะแอดมินลบงานได้')
        instance.delete()

@api_view(['POST'])
def record_attendance(request):
    user = request.user
    if not user.is_authenticated:
        return Response({'error': 'กรุณาเข้าสู่ระบบ'}, status=status.HTTP_401_UNAUTHORIZED)
        
    try:
        employee_obj = Employee.objects.get(user=user)
    except Employee.DoesNotExist:
        return Response({'error': 'บัญชีนี้ยังไม่ได้เชื่อมโยงกับรายชื่อพนักงาน'}, status=status.HTTP_404_NOT_FOUND)

    if not isinstance(request.data, dict):
        return Response({'error': 'ข้อมูลไม่ถูกต้อง'}, status=400)
    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')
    att_type = request.data.get('type')

    if att_type not in ('in', 'out'):
        return Response({'error': 'ประเภทไม่ถูกต้อง'}, status=400)
    try:
        latitude, longitude, accuracy = parse_position(request.data)
    except ValueError as error:
        return Response({'error': str(error)}, status=400)
    distance = distance_meters(ATTENDANCE_CENTER_LATITUDE, ATTENDANCE_CENTER_LONGITUDE, latitude, longitude)
    if distance > ATTENDANCE_RADIUS_METERS:
        return Response({'error': f'อยู่นอกพื้นที่: ห่างจากจุดเช็กชื่อ {distance:.1f} เมตร (อนุญาตไม่เกิน {ATTENDANCE_RADIUS_METERS} เมตร)',
                         'distance_meters': round(distance, 1)}, status=403)

    today = timezone.localdate()
    if att_type == 'in':
        attendance, created = Attendance.objects.get_or_create(
            employee=employee_obj, date=today,
            defaults={'check_in': timezone.now(), 'latitude': latitude, 'longitude': longitude, 'status': 'On Time'}
        )
        if not created:
            changed = Attendance.objects.filter(pk=attendance.pk, check_in__isnull=True).update(
                check_in=timezone.now(), latitude=latitude, longitude=longitude, status='On Time')
            if not changed:
                return Response({'error': 'คุณ Check-in ไปแล้ว'}, status=400)
        return Response({'message': 'Check-in สำเร็จ!'}, status=status.HTTP_200_OK)

    elif att_type == 'out':
        attendance = Attendance.objects.filter(employee=employee_obj, date=today).first()
        if not attendance or not attendance.check_in:
            return Response({'error': 'ยังไม่ได้ Check-in'}, status=status.HTTP_400_BAD_REQUEST)
        if attendance.check_out:
            return Response({'error': 'Check-out ไปแล้ว'}, status=status.HTTP_400_BAD_REQUEST)
        
        changed = Attendance.objects.filter(pk=attendance.pk, check_out__isnull=True).update(check_out=timezone.now())
        if not changed:
            return Response({'error': 'Check-out ไปแล้ว'}, status=400)
        return Response({'message': 'Check-out สำเร็จ!'}, status=status.HTTP_200_OK)

    return Response({'error': 'ประเภทไม่ถูกต้อง'}, status=status.HTTP_400_BAD_REQUEST)

@login_required(login_url='login')
def attendance_host(request):
    if not is_admin(request.user):
        return HttpResponseForbidden('เฉพาะแอดมินเท่านั้น')
    return render(request, 'attendance_host.html')


def local_time(value):
    return timezone.localtime(value).strftime('%H:%M:%S') if value else ''


def csv_response(filename, headers, rows):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow(headers)
    for row in rows:
        safe = []
        for value in row:
            text = '' if value is None else str(value)
            if text.lstrip().startswith(('=', '+', '-', '@')) or text.startswith(('\t', '\r', '\n')):
                text = "'" + text
            safe.append(text)
        writer.writerow(safe)
    return response


@login_required(login_url='login')
@require_POST
def attendance_distance(request):
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict):
            raise ValueError('ข้อมูลไม่ถูกต้อง')
        lat, lng, accuracy = parse_position(data)
    except (ValueError, UnicodeDecodeError) as error:
        return JsonResponse({'error': str(error)}, status=400)
    distance = distance_meters(ATTENDANCE_CENTER_LATITUDE, ATTENDANCE_CENTER_LONGITUDE, lat, lng)
    return JsonResponse({'active': True, 'radius': ATTENDANCE_RADIUS_METERS,
                         'distance': round(distance, 1), 'within': distance <= ATTENDANCE_RADIUS_METERS})
