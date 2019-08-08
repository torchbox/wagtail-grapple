# Generated by Django 2.2.1 on 2019-06-26 08:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("wagtaildocs", "0010_document_file_hash"),
        ("home", "0007_blogpage_cover"),
    ]

    operations = [
        migrations.AddField(
            model_name="blogpage",
            name="book_file",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="wagtaildocs.Document",
            ),
        )
    ]
