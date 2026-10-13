from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('employeeapp', '0008_equipment_equipmentborrow')]
    operations = [
        migrations.CreateModel(
            name='AttendanceHost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('latitude', models.FloatField(default=0)),
                ('longitude', models.FloatField(default=0)),
                ('accuracy', models.FloatField(default=0)),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
                ('active', models.BooleanField(default=False)),
                ('owner_token', models.CharField(blank=True, max_length=64)),
            ],
        ),
    ]
