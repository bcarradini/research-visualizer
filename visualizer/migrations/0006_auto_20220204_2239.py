# Generated by Django 2.2.27 on 2022-02-04 22:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('visualizer', '0005_auto_20220204_2239'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scopusclassification',
            name='category_abbr',
            field=models.CharField(max_length=4),
        ),
        migrations.AlterField(
            model_name='scopusclassification',
            name='category_name',
            field=models.CharField(max_length=64),
        ),
    ]