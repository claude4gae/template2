# Django 5.2.14가 2026-05-23 00:45에 생성

import django.db.models.deletion
import django.db.models.functions.datetime
import django.db.models.functions.text
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DroneEarlyInform',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('line_id', models.CharField(max_length=50)),
                ('main_step', models.CharField(max_length=50)),
                ('custom_end_step', models.CharField(blank=True, max_length=50, null=True)),
                ('updated_by', models.CharField(blank=True, max_length=50, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'drone_early_inform',
                'constraints': [models.UniqueConstraint(fields=('line_id', 'main_step'), name='uniq_dro_erl_inf_ln_id_mn_stp')],
            },
        ),
        migrations.CreateModel(
            name='DroneSOP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sop_key', models.CharField(max_length=300, unique=True)),
                ('line_id', models.CharField(blank=True, max_length=50, null=True)),
                ('sdwt_prod', models.CharField(blank=True, max_length=64, null=True)),
                ('sample_type', models.CharField(blank=True, max_length=50, null=True)),
                ('sample_group', models.CharField(blank=True, max_length=50, null=True)),
                ('eqp_id', models.CharField(blank=True, max_length=50, null=True)),
                ('chamber_ids', models.CharField(blank=True, max_length=50, null=True)),
                ('lot_id', models.CharField(blank=True, max_length=50, null=True)),
                ('proc_id', models.CharField(blank=True, max_length=50, null=True)),
                ('ppid', models.CharField(blank=True, max_length=50, null=True)),
                ('main_step', models.CharField(blank=True, max_length=50, null=True)),
                ('metro_current_step', models.CharField(blank=True, max_length=50, null=True)),
                ('metro_steps', models.CharField(blank=True, max_length=1000, null=True)),
                ('metro_end_step', models.CharField(blank=True, max_length=50, null=True)),
                ('status', models.CharField(blank=True, max_length=50, null=True)),
                ('knox_id', models.CharField(blank=True, max_length=50, null=True)),
                ('comment', models.TextField(blank=True, null=True)),
                ('user_sdwt_prod', models.CharField(blank=True, max_length=64, null=True)),
                ('target_user_sdwt_prod', models.CharField(blank=True, max_length=64, null=True)),
                ('defect_url', models.TextField(blank=True, null=True)),
                ('instant_inform', models.SmallIntegerField(default=0)),
                ('needtosend', models.SmallIntegerField(default=1)),
                ('custom_end_step', models.CharField(blank=True, max_length=50, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_default=django.db.models.functions.datetime.Now())),
                ('updated_at', models.DateTimeField(auto_now=True, db_default=django.db.models.functions.datetime.Now())),
            ],
            options={
                'db_table': 'drone_sop',
                'indexes': [models.Index(fields=['sdwt_prod'], name='idx_dro_sop_sdw_prd'), models.Index(fields=['created_at', 'id'], name='idx_dro_sop_crt_at_id'), models.Index(fields=['user_sdwt_prod', 'created_at', 'id'], name='idx_dro_sop_usr_sdw_prd_dd5e5'), models.Index(fields=['target_user_sdwt_prod', 'created_at', 'id'], name='idx_dro_sop_tgt_crt_id')],
            },
        ),
        migrations.CreateModel(
            name='DroneSopTarget',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('target_user_sdwt_prod', models.CharField(max_length=64)),
                ('line_id', models.CharField(blank=True, default='', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_default=django.db.models.functions.datetime.Now())),
                ('updated_at', models.DateTimeField(auto_now=True, db_default=django.db.models.functions.datetime.Now())),
            ],
            options={
                'db_table': 'drone_sop_target',
                'indexes': [models.Index(fields=['line_id'], name='idx_dro_sop_tgt_line')],
                'constraints': [models.UniqueConstraint(django.db.models.functions.text.Lower('target_user_sdwt_prod'), name='uniq_dro_sop_tgt_key')],
            },
        ),
        migrations.CreateModel(
            name='DroneSopTargetDispatch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('target_code_snapshot', models.CharField(max_length=64)),
                ('target_display_snapshot', models.CharField(blank=True, max_length=128, null=True)),
                ('resolution_status', models.CharField(default='resolved', max_length=32)),
                ('dispatch_type', models.CharField(choices=[('auto', 'Auto'), ('instant', 'Instant'), ('manual', 'Manual'), ('retry', 'Retry')], default='auto', max_length=16)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('dispatching', 'Dispatching'), ('success', 'Success'), ('partial_failed', 'Partial failed'), ('failed', 'Failed'), ('disabled', 'Disabled'), ('cancelled', 'Cancelled')], default='pending', max_length=24)),
                ('comment_override', models.TextField(blank=True, null=True)),
                ('requested_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_default=django.db.models.functions.datetime.Now())),
                ('updated_at', models.DateTimeField(auto_now=True, db_default=django.db.models.functions.datetime.Now())),
                ('requested_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='drone_sop_dispatch_requests', to=settings.AUTH_USER_MODEL)),
                ('sop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='target_dispatches', to='drone.dronesop')),
                ('target', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sop_dispatches', to='drone.dronesoptarget')),
            ],
            options={
                'db_table': 'drone_sop_target_dispatch',
            },
        ),
        migrations.CreateModel(
            name='DroneSopDelivery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('channel', models.CharField(choices=[('jira', 'Jira'), ('mail', 'Mail'), ('messenger', 'Messenger')], max_length=16)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('sending', 'Sending'), ('success', 'Success'), ('failed', 'Failed'), ('disabled', 'Disabled'), ('cancelled', 'Cancelled')], default='pending', max_length=16)),
                ('reason', models.CharField(blank=True, max_length=64, null=True)),
                ('external_key', models.CharField(blank=True, max_length=128, null=True)),
                ('sent_comment', models.TextField(blank=True, null=True)),
                ('sent_step', models.CharField(blank=True, max_length=50, null=True)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('attempt_count', models.PositiveIntegerField(default=0)),
                ('template_key_snapshot', models.CharField(blank=True, max_length=50, null=True)),
                ('channel_config_snapshot', models.JSONField(blank=True, null=True)),
                ('recipient_snapshot', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_default=django.db.models.functions.datetime.Now())),
                ('updated_at', models.DateTimeField(auto_now=True, db_default=django.db.models.functions.datetime.Now())),
                ('sop', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='channel_deliveries', to='drone.dronesop')),
                ('dispatch', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deliveries', to='drone.dronesoptargetdispatch')),
            ],
            options={
                'db_table': 'drone_sop_delivery',
            },
        ),
        migrations.CreateModel(
            name='DroneSopTargetMapping',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sdwt_prod', models.CharField(blank=True, max_length=64, null=True)),
                ('user_sdwt_prod', models.CharField(blank=True, max_length=64, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_default=django.db.models.functions.datetime.Now())),
                ('updated_at', models.DateTimeField(auto_now=True, db_default=django.db.models.functions.datetime.Now())),
                ('target', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mappings', to='drone.dronesoptarget')),
            ],
            options={
                'db_table': 'drone_sop_target_mapping',
            },
        ),
        migrations.CreateModel(
            name='DroneSopTargetRecipient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('channel', models.CharField(choices=[('mail', 'Mail'), ('messenger', 'Messenger')], max_length=16)),
                ('external_knox_id', models.CharField(blank=True, default='', max_length=150)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_default=django.db.models.functions.datetime.Now())),
                ('updated_at', models.DateTimeField(auto_now=True, db_default=django.db.models.functions.datetime.Now())),
                ('target', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recipients', to='drone.dronesoptarget')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='drone_sop_recipients', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'drone_sop_target_recipient',
            },
        ),
        migrations.CreateModel(
            name='DroneSopNeedToSendRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enabled', models.BooleanField(default=False)),
                ('comment_keyword', models.CharField(blank=True, max_length=64, null=True)),
                ('ignore_sample_type', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_default=django.db.models.functions.datetime.Now())),
                ('updated_at', models.DateTimeField(auto_now=True, db_default=django.db.models.functions.datetime.Now())),
                ('target', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='needtosend_rule', to='drone.dronesoptarget')),
            ],
            options={
                'db_table': 'drone_sop_needtosend_rule',
                'indexes': [models.Index(fields=['enabled'], name='idx_dro_nts_rule_en')],
            },
        ),
        migrations.CreateModel(
            name='DroneSopTargetChannelConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('channel', models.CharField(choices=[('jira', 'Jira'), ('mail', 'Mail'), ('messenger', 'Messenger')], max_length=16)),
                ('enabled', models.BooleanField(default=True)),
                ('template_key', models.CharField(blank=True, max_length=50, null=True)),
                ('jira_project_key', models.CharField(blank=True, max_length=64, null=True)),
                ('chatroom_id', models.BigIntegerField(blank=True, null=True)),
                ('force_new_chatroom', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_default=django.db.models.functions.datetime.Now())),
                ('updated_at', models.DateTimeField(auto_now=True, db_default=django.db.models.functions.datetime.Now())),
                ('target', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='channel_configs', to='drone.dronesoptarget')),
            ],
            options={
                'db_table': 'drone_sop_target_channel_config',
                'indexes': [models.Index(fields=['channel', 'enabled'], name='idx_dro_tgt_ch_cfg')],
                'constraints': [models.UniqueConstraint(fields=('target', 'channel'), name='uniq_dro_tgt_ch_cfg'), models.CheckConstraint(condition=models.Q(('channel__in', ['jira', 'mail', 'messenger'])), name='chk_dro_tgt_ch_cfg_ch')],
            },
        ),
        migrations.AddIndex(
            model_name='dronesoptargetdispatch',
            index=models.Index(fields=['sop', 'status'], name='idx_dro_sop_tgt_dsp_sop'),
        ),
        migrations.AddIndex(
            model_name='dronesoptargetdispatch',
            index=models.Index(fields=['target_code_snapshot'], name='idx_dro_sop_tgt_dsp_cd'),
        ),
        migrations.AddConstraint(
            model_name='dronesoptargetdispatch',
            constraint=models.UniqueConstraint(fields=('sop', 'target_code_snapshot'), name='uniq_dro_sop_tgt_dsp'),
        ),
        migrations.AddConstraint(
            model_name='dronesoptargetdispatch',
            constraint=models.CheckConstraint(condition=models.Q(('status__in', ['pending', 'dispatching', 'success', 'partial_failed', 'failed', 'disabled', 'cancelled'])), name='chk_dro_sop_tgt_dsp_st'),
        ),
        migrations.AddIndex(
            model_name='dronesopdelivery',
            index=models.Index(fields=['dispatch', 'channel'], name='idx_dro_sop_dlv_dsp'),
        ),
        migrations.AddIndex(
            model_name='dronesopdelivery',
            index=models.Index(fields=['sop', 'channel'], name='idx_dro_sop_dlv_sop'),
        ),
        migrations.AddIndex(
            model_name='dronesopdelivery',
            index=models.Index(fields=['channel', 'status'], name='idx_dro_sop_dlv_sts'),
        ),
        migrations.AddConstraint(
            model_name='dronesopdelivery',
            constraint=models.UniqueConstraint(fields=('dispatch', 'channel'), name='uniq_dro_sop_dlv_dsp_ch'),
        ),
        migrations.AddConstraint(
            model_name='dronesopdelivery',
            constraint=models.CheckConstraint(condition=models.Q(('status__in', ['pending', 'sending', 'success', 'failed', 'disabled', 'cancelled'])), name='chk_dro_sop_dlv_sts'),
        ),
        migrations.AddConstraint(
            model_name='dronesoptargetmapping',
            constraint=models.CheckConstraint(condition=models.Q(models.Q(('sdwt_prod__isnull', False), models.Q(('sdwt_prod', ''), _negated=True)), models.Q(('user_sdwt_prod__isnull', False), models.Q(('user_sdwt_prod', ''), _negated=True)), _connector='OR'), name='chk_dro_sop_tgt_map_req'),
        ),
        migrations.AddConstraint(
            model_name='dronesoptargetmapping',
            constraint=models.UniqueConstraint(django.db.models.functions.text.Lower('sdwt_prod'), django.db.models.functions.text.Lower('user_sdwt_prod'), condition=models.Q(('sdwt_prod__isnull', False), models.Q(('sdwt_prod', ''), _negated=True), ('user_sdwt_prod__isnull', False), models.Q(('user_sdwt_prod', ''), _negated=True)), name='uniq_dro_tgt_map_pair'),
        ),
        migrations.AddConstraint(
            model_name='dronesoptargetmapping',
            constraint=models.UniqueConstraint(django.db.models.functions.text.Lower('sdwt_prod'), condition=models.Q(('sdwt_prod__isnull', False), models.Q(('sdwt_prod', ''), _negated=True), models.Q(('user_sdwt_prod__isnull', True), ('user_sdwt_prod', ''), _connector='OR')), name='uniq_dro_tgt_map_sdw'),
        ),
        migrations.AddConstraint(
            model_name='dronesoptargetmapping',
            constraint=models.UniqueConstraint(django.db.models.functions.text.Lower('user_sdwt_prod'), condition=models.Q(('user_sdwt_prod__isnull', False), models.Q(('user_sdwt_prod', ''), _negated=True), models.Q(('sdwt_prod__isnull', True), ('sdwt_prod', ''), _connector='OR')), name='uniq_dro_tgt_map_usr'),
        ),
        migrations.AddIndex(
            model_name='dronesoptargetrecipient',
            index=models.Index(fields=['target', 'channel'], name='idx_dro_sop_tgt_rcp_tgt'),
        ),
        migrations.AddIndex(
            model_name='dronesoptargetrecipient',
            index=models.Index(fields=['user'], name='idx_dro_sop_tgt_rcp_usr'),
        ),
        migrations.AddIndex(
            model_name='dronesoptargetrecipient',
            index=models.Index(fields=['external_knox_id'], name='idx_dro_sop_tgt_rcp_ext'),
        ),
        migrations.AddConstraint(
            model_name='dronesoptargetrecipient',
            constraint=models.UniqueConstraint(condition=models.Q(('user__isnull', False)), fields=('target', 'channel', 'user'), name='uniq_dro_sop_tgt_rcp_usr'),
        ),
        migrations.AddConstraint(
            model_name='dronesoptargetrecipient',
            constraint=models.UniqueConstraint(condition=models.Q(('external_knox_id', ''), _negated=True), fields=('target', 'channel', 'external_knox_id'), name='uniq_dro_sop_tgt_rcp_ext'),
        ),
        migrations.AddConstraint(
            model_name='dronesoptargetrecipient',
            constraint=models.CheckConstraint(condition=models.Q(models.Q(('external_knox_id', ''), ('user__isnull', False)), models.Q(('user__isnull', True), models.Q(('external_knox_id', ''), _negated=True)), _connector='OR'), name='chk_dro_sop_tgt_rcp_one'),
        ),
    ]
