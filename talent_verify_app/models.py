from django.db import models
from django.contrib.auth.models import User


class Departments(models.Model):
    department = models.CharField(max_length=200)

    def __str__(self):
        return self.department


class Company(models.Model):
    user = models.ForeignKey(User, related_name='company', on_delete=models.CASCADE, null=True, blank=True)
    department = models.ManyToManyField(Departments)
    name = models.CharField(max_length=200)
    registration_date = models.DateField()
    registration_number = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=200)
    number_of_employees = models.IntegerField()
    contact_phone = models.CharField(max_length=20)
    email_address = models.EmailField()

    def __str__(self):
        return self.name


class Employee(models.Model):
    user = models.OneToOneField(User, related_name='employee', on_delete=models.CASCADE)
    company = models.ForeignKey(Company, related_name='company', on_delete=models.CASCADE)
    department = models.ManyToManyField(Departments)
    id_number = models.CharField(max_length=200, null=True, blank=True)
    class Meta:
        permissions = [
            
        ]

    def __str__(self):
        return f"{self.user.username} {self.user.first_name}"

class DutyRole(models.Model):
    duty_in_role = models.TextField()

    def __str__(self):
        return self.duty_in_role
    
    
class RoleHistory(models.Model):
    employee = models.ForeignKey(Employee, related_name='employee', on_delete=models.CASCADE)
    duties = models.ManyToManyField(DutyRole)
    role = models.CharField(max_length=200)
    date_started = models.DateField()
    date_left = models.DateField(null=True, blank=True)
    company = models.CharField(max_length=200, null=True)

    def __str__(self):
        return f"{self.role}"
    

#the history is only creatd when an employee is added to a new company
class EmployeeCompanyHistory(models.Model):
    employee = models.ForeignKey(Employee, related_name='employee_company_hist', on_delete=models.CASCADE)
    company = models.ForeignKey(Company, related_name='company_hist', on_delete=models.CASCADE)
    


class Upload(models.Model):
    file = models.FileField(upload_to='uploads/')