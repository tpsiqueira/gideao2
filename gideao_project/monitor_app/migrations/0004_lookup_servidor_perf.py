# Generated by Django 5.1.7 on 2025-03-31 11:29

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("monitor_app", "0003_servidor_perf_sonda_perf_analise_perf_amostra_perf"),
    ]

    operations = [
        migrations.CreateModel(
            name="lookup_servidor_perf",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("inicio", models.DateTimeField()),
                ("fim", models.DateTimeField()),
                (
                    "servidor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="monitor_app.servidor_perf",
                    ),
                ),
                (
                    "sonda",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="monitor_app.sonda_perf",
                    ),
                ),
            ],
        ),
    ]
