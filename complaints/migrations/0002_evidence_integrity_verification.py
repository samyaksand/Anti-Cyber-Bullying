from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('complaints', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='evidence',
            name='content_type',
            field=models.CharField(blank=True, editable=False, max_length=100),
        ),
        migrations.AddField(
            model_name='evidence',
            name='file_size',
            field=models.PositiveBigIntegerField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name='evidence',
            name='original_filename',
            field=models.CharField(blank=True, editable=False, max_length=255),
        ),
        migrations.AddField(
            model_name='evidence',
            name='sha256_hash',
            field=models.CharField(blank=True, editable=False, max_length=64),
        ),
        migrations.CreateModel(
            name='EvidenceVerification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('computed_hash', models.CharField(max_length=64)),
                ('result', models.CharField(choices=[('verified', 'Verified'), ('failed', 'Integrity Check Failed')], max_length=10)),
                ('verified_at', models.DateTimeField(auto_now_add=True)),
                ('evidence', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='verifications', to='complaints.evidence')),
                ('verified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-verified_at'],
            },
        ),
    ]
