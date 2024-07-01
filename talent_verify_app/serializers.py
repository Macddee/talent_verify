from rest_framework import serializers
from . import models

class DepartmentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Departments 
        fields="__all__"


class CompanySerializer(serializers.ModelSerializer):
    department = serializers.StringRelatedField(many=True)
    user = serializers.StringRelatedField()
    class Meta:
        model = models.Company
        # fields="__all__"
        exclude = ["id"]


class EmployeeSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    company = serializers.StringRelatedField()
    department = serializers.StringRelatedField(many=True)
    role_history =serializers.StringRelatedField()
    class Meta:
        model = models.Employee
        exclude=['id']
        

class RoleHistorySerializer(serializers.ModelSerializer):
    duties = serializers.StringRelatedField(many=True)
    employee = serializers.StringRelatedField()
    class Meta:
        model = models.RoleHistory
        fields="__all__"

class EmployeeCompanyHistSerializer(serializers.ModelSerializer):
    employee = serializers.StringRelatedField()
    company = serializers.StringRelatedField()
    class Meta:
        model = models.EmployeeCompanyHistory
        fields="__all__"


class UploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Upload
        fields = ('file')