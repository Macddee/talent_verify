# Generated by Django 5.0.6 on 2024-06-22 23:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('talent_verify_app', '0006_dutyrole_rolehistory_duties_delete_employeeduty'),
    ]

    operations = [
        migrations.AddField(
            model_name='rolehistory',
            name='company',
            field=models.CharField(max_length=200, null=True),
        ),
    ]
