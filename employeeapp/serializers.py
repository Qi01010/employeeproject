from rest_framework import serializers
from .models import Employee
from .models import Employee, Task

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__' # แปลงข้อมูลทุกฟิลด์ในตาราง
        
class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'