from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Employee
from .forms import EmployeeForm

def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

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
    
    # แบ่งหน้า 4 คนต่อ 1 หน้า
    paginator = Paginator(employee_list, 4)
    page_number = request.GET.get('page', 1)
    employees = paginator.get_page(page_number)

    return render(request, 'index.html', {'employees': employees, 'search_query': search_query})

@user_passes_test(is_admin, login_url='login')
def employee(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "บันทึกข้อมูลเรียบร้อย")
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
            messages.success(request, "แก้ไขข้อมูลเรียบร้อย")
            return redirect('index')
    else:
        form = EmployeeForm(instance=emp)
    return render(request, 'edit.html', {'form': form, 'emp': emp})

@user_passes_test(is_admin, login_url='login')
def delete(request, emp_id):
    emp = get_object_or_404(Employee, id=emp_id)
    emp.delete()
    messages.success(request, "ลบข้อมูลเรียบร้อย")
    return redirect('index')