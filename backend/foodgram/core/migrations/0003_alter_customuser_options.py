# Generated by Django 4.2.15 on 2024-09-27 18:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_alter_customuser_is_active_alter_customuser_is_staff_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='customuser',
            options={'ordering': ('email',), 'verbose_name': 'пользователь', 'verbose_name_plural': 'Пользователи'},
        ),
    ]
