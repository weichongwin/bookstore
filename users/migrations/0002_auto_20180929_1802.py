# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('is_delete', models.BooleanField(default=False, verbose_name='是否删除')),
                ('creare_time', models.DateField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateField(auto_now=True, verbose_name='更新时间')),
                ('recipient_name', models.CharField(max_length=32, verbose_name='收件人')),
                ('recipient_addr', models.CharField(max_length=256, verbose_name='收件地址')),
                ('zip_code', models.CharField(max_length=6, verbose_name='邮政编码')),
                ('recipient_phone', models.CharField(max_length=11, verbose_name='联系电话')),
                ('is_default', models.BooleanField(default=False, verbose_name='是否默认')),
            ],
            options={
                'db_table': 's_user_address',
                'verbose_name_plural': '地址',
                'verbose_name': '地址',
            },
        ),
        migrations.AlterModelOptions(
            name='passport',
            options={'verbose_name_plural': '用户', 'verbose_name': '用户'},
        ),
        migrations.AddField(
            model_name='address',
            name='passport',
            field=models.ForeignKey(to='users.Passport', verbose_name='账户'),
        ),
    ]
