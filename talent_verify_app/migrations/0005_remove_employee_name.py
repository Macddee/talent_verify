# Generated by Django 5.0.6 on 2024-06-21 23:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('talent_verify_app', '0004_remove_employee_department_employee_department'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='employee',
            name='name',
        ),
    ]