from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cyberbullying', '0003_auto_20210227_1950'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Complaint',
        ),
    ]
