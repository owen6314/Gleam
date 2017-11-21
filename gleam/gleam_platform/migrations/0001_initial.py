# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-11-19 07:52
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import gleam_platform.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0008_alter_user_username_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('first_name', models.CharField(blank=True, max_length=30, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=30, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('email', models.EmailField(max_length=80, unique=True, verbose_name='email address')),
                ('type', models.CharField(choices=[('O', 'Organizer'), ('C', 'Contestant')], max_length=2)),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', gleam_platform.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Contest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('submit_begin_time', models.DateField()),
                ('submit_end_time', models.DateField()),
                ('release_time', models.DateField()),
                ('description', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Contestant',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nick_name', models.CharField(max_length=32)),
                ('school', models.CharField(max_length=128)),
                ('gender', models.CharField(choices=[('M', 'male'), ('F', 'female'), ('O', 'others')], default='O', max_length=2)),
            ],
        ),
        migrations.CreateModel(
            name='Dataset',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dataset', models.FileField(upload_to=gleam_platform.models.generate_dataset_filename)),
                ('contest', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gleam_platform.Contest')),
            ],
        ),
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contestant', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='gleam_platform.Contestant')),
            ],
        ),
        migrations.CreateModel(
            name='Organizer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('organization', models.CharField(max_length=128, verbose_name='组织')),
            ],
            options={
                'verbose_name': 'Organizer',
            },
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.DecimalField(decimal_places=2, max_digits=4)),
                ('data', models.FileField(upload_to=gleam_platform.models.generate_submission_filename)),
                ('time', models.DateField()),
                ('contest', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gleam_platform.Contest')),
            ],
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32)),
                ('contest', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gleam_platform.Contest')),
                ('members', models.ManyToManyField(through='gleam_platform.Membership', to='gleam_platform.Contestant')),
            ],
        ),
        migrations.CreateModel(
            name='Tournament',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('description', models.TextField()),
                ('status', models.IntegerField()),
                ('image', models.ImageField(blank=True, null=True, upload_to='')),
                ('register_begin_time', models.DateField()),
                ('register_end_time', models.DateField()),
                ('organizer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gleam_platform.Organizer')),
            ],
        ),
        migrations.AddField(
            model_name='submission',
            name='team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gleam_platform.Team'),
        ),
        migrations.AddField(
            model_name='membership',
            name='team',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='gleam_platform.Team'),
        ),
        migrations.AddField(
            model_name='contest',
            name='tournament',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gleam_platform.Tournament'),
        ),
        migrations.AddField(
            model_name='user',
            name='contestant_profile',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='gleam_platform.Contestant'),
        ),
        migrations.AddField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups'),
        ),
        migrations.AddField(
            model_name='user',
            name='organizer_profile',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='gleam_platform.Organizer'),
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions'),
        ),
    ]
