from datetime import timedelta
from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.utils import timezone
from .models import Employee, Task, Attendance, LeaveRequest, Equipment, EquipmentBorrow
from .geofence import (ATTENDANCE_CENTER_LATITUDE, ATTENDANCE_CENTER_LONGITUDE,
                       distance_meters)


class AccessAndReportsTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user('admin', is_staff=True)
        self.user = User.objects.create_user('worker')
        self.other = User.objects.create_user('other')
        self.emp = Employee.objects.create(fname='Worker', lname='One', user=self.user, salary=Decimal('30000'))
        self.emp2 = Employee.objects.create(fname='Other', lname='Two', user=self.other, salary=Decimal('98765'), address='PRIVATE_ADDRESS_123')
        self.task = Task.objects.create(employee=self.emp, title='Own', due_date=timezone.localdate())
        self.task2 = Task.objects.create(employee=self.emp2, title='OtherTask', due_date=timezone.localdate())
        self.client.force_login(self.user)

    def test_leave_owner_and_validation(self):
        today=timezone.localdate()
        data={'employee':self.emp2.pk,'leave_type':'sick','start_date':str(today),'end_date':str(today),'reason':'Test','status':'approved'}
        self.assertEqual(self.client.post('/leave/request/',data).status_code,302)
        leave=LeaveRequest.objects.get()
        self.assertEqual(leave.employee_id,self.emp.pk)
        self.assertEqual(leave.status,'pending')
        data['end_date']=str(today-timedelta(days=1))
        self.assertEqual(self.client.post('/leave/request/',data).status_code,200)
        self.assertEqual(LeaveRequest.objects.count(),1)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.post('/leave/request/',data).status_code,403)

    def test_api_and_task_ownership(self):
        self.assertEqual(self.client.get('/api/employees/').status_code,403)
        self.assertEqual(self.client.patch(f'/api/tasks/{self.task2.pk}/',{'status':'completed'},content_type='application/json').status_code,404)
        self.assertEqual(self.client.patch(f'/api/tasks/{self.task.pk}/',{'status':'completed'},content_type='application/json').status_code,200)
        self.assertEqual(self.client.patch(f'/api/tasks/{self.task.pk}/',{'employee':self.emp2.pk},content_type='application/json').status_code,403)
        self.assertEqual(self.client.delete(f'/api/tasks/{self.task.pk}/').status_code,403)
        self.assertEqual(self.client.post(f'/update-task-status/{self.task2.pk}/',{'status':'completed'}).status_code,404)

    def test_private_fields_and_post_only(self):
        response=self.client.get('/')
        self.assertNotContains(response,'PRIVATE_ADDRESS_123')
        self.assertNotContains(response,'98765')
        self.assertNotContains(response,'OtherTask')
        self.client.force_login(self.admin)
        leave=LeaveRequest.objects.create(employee=self.emp,leave_type='sick',start_date=timezone.localdate(),end_date=timezone.localdate(),reason='x')
        eq=Equipment.objects.create(name='Laptop',serial_number='abc')
        borrow=EquipmentBorrow.objects.create(employee=self.emp,equipment=eq)
        for url in [f'/delete/{self.emp.pk}/',f'/delete-task/{self.task.pk}/',f'/leave/update/{leave.pk}/approve/',f'/equipment/return/{borrow.pk}/']:
            self.assertEqual(self.client.get(url).status_code,405)
        csrf=Client(enforce_csrf_checks=True);csrf.force_login(self.admin)
        self.assertEqual(csrf.post(f'/delete-task/{self.task.pk}/').status_code,403)
        self.assertEqual(self.client.post(f'/leave/update/{leave.pk}/approve/').status_code,302)
        self.assertEqual(self.client.get('/leave/approvals/').status_code,200)
        self.assertEqual(self.client.get('/equipment/').status_code,200)

    def test_unique_and_geofence(self):
        p={'latitude':ATTENDANCE_CENTER_LATITUDE,'longitude':ATTENDANCE_CENTER_LONGITUDE,'accuracy':10,'type':'in'}
        self.assertEqual(self.client.post('/api/attendance/record/',p,content_type='application/json').status_code,200)
        self.assertEqual(self.client.post('/api/attendance/record/',p,content_type='application/json').status_code,400)
        with self.assertRaises(IntegrityError):
            with transaction.atomic(): Attendance.objects.create(employee=self.emp)
        p['latitude']=ATTENDANCE_CENTER_LATITUDE + 201 / 111194
        self.assertEqual(self.client.post('/api/attendance/record/',p,content_type='application/json').status_code,403)
        d=self.client.post('/attendance/distance/',p,content_type='application/json').json()
        self.assertFalse(d['within']);self.assertTrue(d['active'])
        p['latitude']=ATTENDANCE_CENTER_LATITUDE + 199 / 111194
        d=self.client.post('/attendance/distance/',p,content_type='application/json').json()
        self.assertTrue(d['within'])
        self.assertAlmostEqual(distance_meters(ATTENDANCE_CENTER_LATITUDE, ATTENDANCE_CENTER_LONGITUDE,
                                               p['latitude'], p['longitude']),199,delta=0.1)
        self.client.force_login(self.admin)
        self.assertContains(self.client.get('/attendance/host/'),'16.4511111111')

    def test_report_and_payroll(self):
        att=Attendance.objects.create(employee=self.emp,check_in=timezone.now())
        self.client.force_login(self.admin)
        month=timezone.localdate().strftime('%Y-%m')
        params={'month':month,'employee':self.emp.pk,'export':'csv'}
        response=self.client.get('/attendance/report/',params)
        self.assertEqual(response.status_code,200)
        self.assertIn('text/csv',response['Content-Type'])
        self.assertContains(response,'Worker')
        self.assertNotContains(response,'Other')
        self.assertEqual(self.client.get('/attendance/report/',{'start':'bad','export':'csv'}).status_code,400)
        response=self.client.get('/payroll/',{'month':month,'mode':'monthly','divisor':30})
        self.assertEqual(response.context['payroll_data'][0]['total_pay'],Decimal('30000'))
        response=self.client.get('/payroll/',{'month':month,'mode':'attendance','divisor':30})
        self.assertEqual(response.context['payroll_data'][0]['total_pay'],Decimal('1000'))
        self.assertEqual(self.client.get('/payroll/',{'month':month,'mode':'attendance','divisor':0,'export':'csv'}).status_code,400)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get('/attendance/report/',params).status_code,302)

    def test_radius_context(self):
        from unittest.mock import patch
        with patch('employeeapp.context_processors.ATTENDANCE_RADIUS_METERS',321):
            self.assertContains(self.client.get('/attendance/'),'321')

    def test_employee_menu_opens_add_form_without_resume_assistant(self):
        self.client.force_login(self.admin)
        home = self.client.get('/')
        self.assertContains(home, 'href="/employee/">เพิ่มพนักงานใหม่</a>')
        self.assertContains(home, 'href="/attendance/report/"')
        self.assertContains(home, 'ประวัติลงเวลา</a>')
        self.assertNotContains(home, 'href="/attendance/report/">จัดการข้อมูลพนักงาน</a>')
        add_page = self.client.get('/employee/')
        self.assertContains(add_page, 'เพิ่มพนักงานใหม่')
        self.assertNotContains(add_page, 'ระบบผู้ช่วย')
        self.assertNotContains(add_page, 'parse_resume')
