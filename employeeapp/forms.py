from django import forms
from .models import Employee

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['fname', 'lname', 'address', 'gender', 'birthdate', 'department', 'salary', 'pics']
        widgets = {
            'fname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ระบุชื่อจริง'}),
            'lname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ระบุนามสกุล'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'ระบุที่อยู่'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'birthdate': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'ระบุเงินเดือน'}),
            'pics': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'fname': 'ชื่อจริง',
            'lname': 'นามสกุล',
            'address': 'ที่อยู่',
            'gender': 'เพศ',
            'birthdate': 'วันเกิด',
            'department': 'แผนกงาน',
            'salary': 'เงินเดือน (บาท)',
            'pics': 'รูปถ่ายพนักงาน',
        }