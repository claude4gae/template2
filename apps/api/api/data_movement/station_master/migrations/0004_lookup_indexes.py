# Django 5.2.14가 2026-06-22에 생성

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("station_master", "0003_stationmaster_addr_book_id_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="stationmaster",
            name="station_lookup",
            field=models.CharField(blank=True, max_length=40, null=True),
        ),
        migrations.AddField(
            model_name="stationmaster",
            name="sdwt_prod_lookup",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="stationmaster",
            name="prc_group_lookup",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.RunSQL(
            """
            UPDATE station_master
            SET
                station_lookup = UPPER(NULLIF(TRIM(station), '')),
                sdwt_prod_lookup = UPPER(NULLIF(TRIM(sdwt_prod), '')),
                prc_group_lookup = UPPER(NULLIF(TRIM(prc_group), ''))
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AddIndex(
            model_name="stationmaster",
            index=models.Index(
                fields=["sdwt_prod_lookup", "prc_group_lookup", "station"],
                name="idx_st_sdwt_prc_st",
            ),
        ),
        migrations.AddIndex(
            model_name="stationmaster",
            index=models.Index(
                fields=["prc_group_lookup", "sdwt_prod_lookup", "station"],
                name="idx_st_prc_sdwt_st",
            ),
        ),
        migrations.AddIndex(
            model_name="stationmaster",
            index=models.Index(fields=["station_lookup"], name="idx_st_station_lkp"),
        ),
        migrations.AddIndex(
            model_name="stationmaster",
            index=models.Index(fields=["floor_line_id"], name="idx_st_floor_ln"),
        ),
    ]
