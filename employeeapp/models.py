from django.db import models

class Employee(models.Model):
    fname = models.CharField(max_length=50)
    lname = models.CharField(max_length=50)
    address = models.TextField()
    gender = models.CharField(
        max_length=5,
        choices=[('ชาย', 'ชาย'), ('หญิง', 'หญิง')],
        default='ชาย'
    )
    birthdate = models.DateField()
    department = models.CharField(
        max_length=50,
        choices=[('ไอที', 'ไอที'), ('การเงิน', 'การเงิน'), ('ช่างซ่อม', 'ช่างซ่อม')],
        default='ไอที'
    )
    salary = models.IntegerField()
    pics = models.ImageField(upload_to="images", blank=True)

    def __str__(self):
        return f"{self.fname} {self.lname}"