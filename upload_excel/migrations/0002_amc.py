# Generated by Django 5.0.6 on 2025-02-20 06:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('upload_excel', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AMC',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
            ],
        ),
    ]
