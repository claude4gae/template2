# Django 5.2.14가 2026-06-20 07:29에 생성했습니다.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('station_master', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='stationmaster',
            name='addr_book_id',
        ),
        migrations.RemoveField(
            model_name='stationmaster',
            name='purge_target_yn',
        ),
        migrations.AddField(
            model_name='stationmaster',
            name='eff_loss_type',
            field=models.CharField(blank=True, max_length=40, null=True),
        ),
        migrations.AddField(
            model_name='stationmaster',
            name='incld_reason_detail_code',
            field=models.CharField(blank=True, max_length=40, null=True),
        ),
        migrations.AddField(
            model_name='stationmaster',
            name='maker_name',
            field=models.CharField(blank=True, max_length=120, null=True),
        ),
        migrations.AlterField(
            model_name='stationmaster',
            name='ch_main',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='stationmaster',
            name='in_line',
            field=models.CharField(blank=True, max_length=5, null=True),
        ),
        migrations.AlterField(
            model_name='stationmaster',
            name='sdwt_prod',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
