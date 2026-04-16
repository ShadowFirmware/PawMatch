from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth_app', '0005_bitacoraevento'),
        ('authtoken', '0003_tokenproxy'),
    ]

    operations = [
        migrations.CreateModel(
            name='TokenActividad',
            fields=[
                ('token', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    primary_key=True,
                    related_name='actividad',
                    serialize=False,
                    to='authtoken.token',
                )),
                ('ultima_actividad', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'token_actividad',
            },
        ),
    ]
