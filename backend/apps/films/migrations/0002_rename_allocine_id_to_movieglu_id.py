from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('films', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='cinemachain',
            old_name='allocine_id',
            new_name='movieglu_id',
        ),
        migrations.RenameField(
            model_name='cinema',
            old_name='allocine_id',
            new_name='movieglu_id',
        ),
    ]
