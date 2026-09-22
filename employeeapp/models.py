from django.db import models
from django.contrib.auth.models import User
class Employee(models.Model):
    GENDER_CHOICES = [
        ('ชาย', 'ชาย'),
        ('หญิง', 'หญิง'),
        ('อื่นๆ', 'อื่นๆ'),
    ]

    fname = models.CharField(max_length=100, verbose_name="ชื่อจริง")
    lname = models.CharField(max_length=100, verbose_name="นามสกุล")
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='ชาย', verbose_name="เพศ")
    birthdate = models.DateField(blank=True, null=True, verbose_name="วัน/เดือน/ปีเกิด") # เพิ่มฟิลด์วันเกิด
    department = models.CharField(max_length=100, blank=True, null=True, verbose_name="แผนก")
    salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="เงินเดือน")
    address = models.TextField(blank=True, null=True, verbose_name="ที่อยู่")
    image = models.ImageField(upload_to='employee_images/', blank=True, null=True, verbose_name="รูปภาพพนักงาน")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="วันที่บันทึก")
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='employee_record')
    
    def __str__(self):
        return f"{self.fname} {self.lname}"

class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'รอดำเนินการ'),
        ('in_progress', 'กำลังดำเนินการ'),
        ('completed', 'เสร็จสิ้น'),
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='tasks', verbose_name="ผู้รับผิดชอบงาน")
    title = models.CharField(max_length=200, verbose_name="ชื่องาน")
    description = models.TextField(blank=True, null=True, verbose_name="รายละเอียดงาน")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="สถานะงาน")
    due_date = models.DateField(verbose_name="กำหนดส่ง")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="วันที่มอบหมาย")

    def __str__(self):
        return f"{self.title} ({self.employee.fname})"

class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances', verbose_name="พนักงาน")
    date = models.DateField(auto_now_add=True, verbose_name="วันที่ลงเวลา")
    check_in = models.DateTimeField(null=True, blank=True, verbose_name="เวลาเข้างาน")
    check_out = models.DateTimeField(null=True, blank=True, verbose_name="เวลาออกงาน")
    latitude = models.FloatField(null=True, blank=True, verbose_name="ละติจูด (GPS)")
    longitude = models.FloatField(null=True, blank=True, verbose_name="ลองจิจูด (GPS)")
    status = models.CharField(max_length=50, default='On Time', verbose_name="สถานะการเข้างาน")

    def __str__(self):
        return f"{self.employee.fname} - วันที่: {self.date}"
class LeaveRequest(models.Model):
    LEAVE_TYPES = [
        ('sick', 'ลาป่วย'),
        ('personal', 'ลากิจ'),
        ('annual', 'พักร้อน'),
    ]
    STATUS_CHOICES = [
        ('pending', 'รออนุมัติ'),
        ('approved', 'อนุมัติแล้ว'),
        ('rejected', 'ไม่อนุมัติ'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leaves', verbose_name="พนักงาน")
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES, verbose_name="ประเภทการลา")
    start_date = models.DateField(verbose_name="ตั้งแต่วันที่")
    end_date = models.DateField(verbose_name="ถึงวันที่")
    reason = models.TextField(verbose_name="เหตุผลการลา")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="สถานะการอนุมัติ")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="วันที่ยื่นคำขอ")

    def __str__(self):
        return f"{self.employee} - {self.get_leave_type_display()} ({self.get_status_display()})"
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile') # เพิ่ม related_name ตรงนี้
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="เบอร์โทรศัพท์")
    image = models.ImageField(upload_to='profiles/', blank=True, null=True, verbose_name="รูปโปรไฟล์")

    def __str__(self):
        return f"Profile of {self.user.username}"
    
# 💻 1. โมเดลเก็บข้อมูลอุปกรณ์ในบริษัท
class Equipment(models.Model):
    name = models.CharField(max_length=100) # ชื่ออุปกรณ์ (เช่น โน้ตบุ๊ก Dell, โปรเจกเตอร์)
    serial_number = models.CharField(max_length=50, unique=True) # Serial Number หรือรหัสโค้ด
    category = models.CharField(max_length=50, blank=True, null=True) # หมวดหมู่
    status = models.CharField(
        max_length=20, 
        choices=[('available', 'พร้อมใช้งาน'), ('borrowed', 'กำลังถูกยืม'), ('maintenance', 'ซ่อมบำรุง')], 
        default='available'
    )
    
    def __str__(self):
        return f"{self.name} ({self.serial_number})"

# 📋 2. โมเดลบันทึกประวัติการยืม-คืน
class EquipmentBorrow(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    borrow_date = models.DateField(auto_now_add=True)
    return_date = models.DateField(blank=True, null=True)
    status = models.CharField(
        max_length=20, 
        choices=[('borrowing', 'กำลังยืม'), ('returned', 'คืนแล้ว')], 
        default='borrowing'
    )

    def __str__(self):
        return f"{self.employee} ยืม {self.equipment}"