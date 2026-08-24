from django import forms
from employeeapp.models import Employee

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = '__all__'
        labels = {
            'fname': 'ชื่อ',
            'lname': 'นามสกุล',
            'address': 'ที่อยู่',
            'gender': 'เพศ',
            'birthdate': 'วันเกิด',
            'department': 'แผนก',
            'salary': 'เงินเดือน',
            'pics': 'รูปภาพ',
        }
        widgets = {
            'fname': forms.TextInput(attrs={'class': 'form-control'}),
            'lname': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'gender': forms.RadioSelect(),
            'birthdate': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control'}),
            'pics': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }