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
        }

class LeaveForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['employee', 'leave_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'leave_type': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'ระบุเหตุผลการลา...'}),
        }

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone', 'image']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ระบุเบอร์โทรศัพท์...'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }