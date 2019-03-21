from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

if settings.MULTITENANCY:
    run_before_multitenancy = [
        ('multitenancy', '0001_initial'),
    ]
else:
    run_before_multitenancy = []


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TestModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField()),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
        ),
        migrations.CreateModel(
            name='TestChildModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField()),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='children', to='fakeapp.TestModel'))
            ],
            options={
            },
        ),
        migrations.CreateModel(
            name='TestGrandChildModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField()),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='children', to='fakeapp.TestChildModel'))
            ],
            options={
            },
        ),
        migrations.CreateModel(
            name='TestNoMtModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField()),
            ],
            options={
            },
        ),
    ]
