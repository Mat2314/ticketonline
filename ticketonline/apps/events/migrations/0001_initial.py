# Generated by Django 2.2.19 on 2021-02-21 09:38

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=512)),
                ('date', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='Reservation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('CANCELLED', 'CANCELLED'), ('PENDING', 'PENDING'), ('COMPLETED', 'COMPLETED')], default='PENDING', max_length=32)),
                ('pending_until', models.DateTimeField()),
                ('reservation_date', models.DateTimeField(auto_now_add=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to='events.Event')),
            ],
        ),
    ]
