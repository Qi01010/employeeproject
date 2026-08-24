from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from employeeapp.models import Employee
from employeeapp.forms import EmployeeForm

# หน้าหลัก: แสดงข้อมูล + ค้นหา + แบ่งหน้า
def index(request):
    search_query = request.GET.get('search', '')
    if search_query:
        employee_list = Employee.objects.filter(fname__icontains=search_query)
    else:
        employee_list = Employee.objects.all().order_by('-id')

    paginator = Paginator(employee_list, 4)
    page_number = request.GET.get('page')
    employees = paginator.get_page(page_number)

    return render(request, 'index.html', {
        'all_employee': employees,
        'search_query': search_query
    })

# เพิ่มข้อมูลพนักงาน
def employee(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'บันทึกข้อมูลเรียบร้อย')
            return redirect('index')
    else:
        form = EmployeeForm()
    return render(request, 'employee.html', {'form': form})

# แก้ไขข้อมูลพนักงาน
def edit(request, emp_id):
    emp = get_object_or_404(Employee, pk=emp_id)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=emp)
        if form.is_valid():
            form.save()
            messages.success(request, 'แก้ไขข้อมูลเรียบร้อย')
            return redirect('index')
    else:
        form = EmployeeForm(instance=emp)
    return render(request, 'edit.html', {'form': form, 'emp': emp})

# ลบข้อมูลพนักงาน
def delete(request, emp_id):
    emp = get_object_or_404(Employee, pk=emp_id)
    emp.delete()
    messages.warning(request, 'ลบข้อมูลเรียบร้อย')
    return redirect('index')