from django.urls import path
from employeeapp import views

urlpatterns = [
    path('', views.index, name='index'),
    path('employee/', views.employee, name='employee'),
    path('edit/<int:emp_id>/', views.edit, name='edit'),
    path('delete/<int:emp_id>/', views.delete, name='delete'),
]