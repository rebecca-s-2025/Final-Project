# Generated by Django 5.1.3 on 2025-02-22 17:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_alter_studentnote_file_textbookdrop'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='textbookdrop',
            options={'ordering': ['-created_on'], 'verbose_name': 'Textbook Drop'},
        ),
        migrations.RemoveField(
            model_name='textbookdrop',
            name='textbook',
        ),
        migrations.AddField(
            model_name='textbookdrop',
            name='textbook_isbn',
            field=models.CharField(default='', max_length=13),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='textbookdrop',
            name='textbook_title',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='textbookdrop',
            name='drop_date',
            field=models.DateTimeField(),
        ),
    ]
