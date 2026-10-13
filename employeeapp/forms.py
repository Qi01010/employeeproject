from django import forms
from .models import Employee, Task, Attendance, LeaveRequest, Profile

class EmployeeForm(forms.ModelForm):
    DEPARTMENT_CHOICES = [
        ('', '-- กรุณาเลือกแผนกงาน --'),
        ('ไอที', 'ไอที'),
        ('ช่างซ่อม', 'ช่างซ่อม'),
        ('การเงิน', 'การเงิน'),
        ('บุคคล', 'บุคคล'),
        ('การตลาด', 'การตลาด'),
    ]

    department = forms.ChoiceField(
        choices=DEPARTMENT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="แผนกงาน"
    )

    class Meta:
        model = Employee
        fields = ['fname', 'lname', 'gender', 'birthdate', 'department', 'salary', 'address', 'image']
        widgets = {
            'fname': forms.TextInput(attrs={'class': 'form-control'}),
            'lname': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'birthdate': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class LeaveForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'leave_type': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'ระบุเหตุผลการลา...'}),
        }

    def clean(self):
        data = super().clean()
        if data.get('start_date') and data.get('end_date') and data['end_date'] < data['start_date']:
            self.add_error('end_date', 'วันสิ้นสุดต้องไม่ก่อนวันเริ่มลา')
        return data

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone', 'image']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ระบุเบอร์โทรศัพท์...'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class ReportFilterForm(forms.Form):
    month = forms.DateField(required=False, input_formats=['%Y-%m'], widget=forms.DateInput(
        attrs={'type': 'month', 'class': 'form-control'}, format='%Y-%m'), label='เดือน')
    start = forms.DateField(required=False, widget=forms.DateInput(
        attrs={'type': 'date', 'class': 'form-control'}), label='ตั้งแต่วันที่')
    end = forms.DateField(required=False, widget=forms.DateInput(
        attrs={'type': 'date', 'class': 'form-control'}), label='ถึงวันที่')
    employee = forms.ModelChoiceField(queryset=Employee.objects.all(), required=False,
        widget=forms.Select(attrs={'class': 'form-select'}), label='พนักงาน')

    def clean(self):
        import calendar
        from django.utils import timezone
        data = super().clean()
        start, end, month = data.get('start'), data.get('end'), data.get('month')
        if bool(start) != bool(end):
            raise forms.ValidationError('กรุณาเลือกวันเริ่มต้นและสิ้นสุดให้ครบ')
        if not start:
            start = month or timezone.localdate()
            end = start.replace(day=calendar.monthrange(start.year, start.month)[1]) if month else start
        if end < start or (end-start).days > 366:
            raise forms.ValidationError('ช่วงวันที่ต้องเรียงลำดับและไม่เกิน 367 วัน')
        data.update(start=start, end=end)
        return data


class PayrollFilterForm(forms.Form):
    month = forms.DateField(input_formats=['%Y-%m'], widget=forms.DateInput(attrs={'type': 'month'}, format='%Y-%m'), label='เดือน')
    mode = forms.ChoiceField(choices=[('monthly', 'เงินเดือนตั้งต้น ไม่หักอัตโนมัติ'), ('attendance', 'ประมาณการตามวันที่ลงเวลา')], label='วิธีคำนวณ')
    divisor = forms.DecimalField(min_value=1, max_value=366, max_digits=5, decimal_places=2, initial=30, label='จำนวนวันหาร (สำหรับประมาณการ)')
