from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pets_app', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mascota',
            name='foto_url',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='mascota',
            name='género',
            field=models.CharField(
                blank=True,
                choices=[('Macho', 'Macho'), ('Hembra', 'Hembra'), ('Otro', 'Otro')],
                default='Otro',
                max_length=10,
            ),
        ),
    ]
