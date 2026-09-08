import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='VwEntityCoverage',
            fields=[
                ('metric', models.TextField(primary_key=True, serialize=False)),
                ('value', models.BigIntegerField(null=True)),
            ],
            options={
                'db_table': 'vw_entity_coverage',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='VwReport',
            fields=[
                ('report_id', models.TextField(primary_key=True, serialize=False)),
                ('title', models.TextField(null=True)),
                ('description', models.TextField(null=True)),
                ('actions', models.TextField(null=True)),
                ('analysis', models.TextField(null=True)),
                ('creation_date', models.DateField(null=True)),
                ('publication_date', models.DateField(null=True)),
                ('report_date', models.DateField(null=True)),
                ('updated_at', models.DateTimeField(null=True)),
                ('classification', models.TextField(null=True)),
                ('evidence_type', models.TextField(null=True)),
                ('importance', models.TextField(null=True)),
                ('observation_source', models.TextField(null=True)),
                ('threat_type', models.TextField(null=True)),
                ('country_group_key', models.CharField(max_length=32, null=True)),
                ('entity_group_key', models.CharField(max_length=32, null=True)),
                ('group_group_key', models.CharField(max_length=32, null=True)),
            ],
            options={
                'db_table': 'vw_report',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='VwReportCountry',
            fields=[
                ('report_id', models.TextField(primary_key=True, serialize=False)),
                ('title', models.TextField(null=True)),
                ('report_date', models.DateField(null=True)),
                ('classification', models.TextField(null=True)),
                ('importance', models.TextField(null=True)),
                ('threat_type', models.TextField(null=True)),
                ('weight_factor', models.FloatField(null=True)),
                ('is_unknown_member', models.BooleanField(default=False)),
                ('country_id', models.BigIntegerField(null=True)),
                ('country_name', models.TextField(null=True)),
            ],
            options={
                'db_table': 'vw_report_country',
                'abstract': False,
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='VwReportEntity',
            fields=[
                ('report_id', models.TextField(primary_key=True, serialize=False)),
                ('title', models.TextField(null=True)),
                ('report_date', models.DateField(null=True)),
                ('classification', models.TextField(null=True)),
                ('importance', models.TextField(null=True)),
                ('threat_type', models.TextField(null=True)),
                ('weight_factor', models.FloatField(null=True)),
                ('is_unknown_member', models.BooleanField(default=False)),
                ('entity_id', models.BigIntegerField(null=True)),
                ('entity_name_en', models.TextField(null=True)),
                ('entity_name_ar', models.TextField(null=True)),
                ('cti_id', models.TextField(null=True)),
                ('prm_id', models.TextField(null=True)),
                ('sector', models.TextField(null=True)),
                ('category', models.TextField(null=True)),
                ('entity_type', models.TextField(null=True)),
                ('entity_country', models.TextField(null=True)),
                ('is_cti_entity', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'vw_report_entity',
                'abstract': False,
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='VwReportGroup',
            fields=[
                ('report_id', models.TextField(primary_key=True, serialize=False)),
                ('title', models.TextField(null=True)),
                ('report_date', models.DateField(null=True)),
                ('classification', models.TextField(null=True)),
                ('importance', models.TextField(null=True)),
                ('threat_type', models.TextField(null=True)),
                ('weight_factor', models.FloatField(null=True)),
                ('is_unknown_member', models.BooleanField(default=False)),
                ('group_id', models.BigIntegerField(null=True)),
                ('group_name', models.TextField(null=True)),
            ],
            options={
                'db_table': 'vw_report_group',
                'abstract': False,
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='DimClassification',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('classification_name', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'classifications',
                'db_table': 'dim_classification',
            },
        ),
        migrations.CreateModel(
            name='DimCountry',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('country_name', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'countries',
                'db_table': 'dim_country',
            },
        ),
        migrations.CreateModel(
            name='DimEvidenceType',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('evidence_type_name', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'evidence types',
                'db_table': 'dim_evidence_type',
            },
        ),
        migrations.CreateModel(
            name='DimGroup',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('group_name', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'threat groups',
                'db_table': 'dim_group',
            },
        ),
        migrations.CreateModel(
            name='DimImportanceLevel',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('importance_level', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'importance levels',
                'db_table': 'dim_importance_level',
            },
        ),
        migrations.CreateModel(
            name='DimSource',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('source_name', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'sources',
                'db_table': 'dim_source',
            },
        ),
        migrations.CreateModel(
            name='DimThreatType',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('threat_type_name', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'threat types',
                'db_table': 'dim_threat_type',
            },
        ),
        migrations.CreateModel(
            name='DimEntity',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('cti_id', models.TextField(blank=True, null=True)),
                ('prm_id', models.TextField(blank=True, null=True)),
                ('entity_name_en', models.TextField(blank=True, null=True)),
                ('entity_name_ar', models.TextField(blank=True, null=True)),
                ('country', models.TextField(blank=True, null=True)),
                ('category', models.TextField(blank=True, null=True)),
                ('sector', models.TextField(blank=True, null=True)),
                ('entity_type', models.TextField(blank=True, null=True)),
                ('domain', models.TextField(blank=True, null=True)),
                ('is_cti_entity', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name_plural': 'entities',
                'db_table': 'dim_entity',
                'indexes': [models.Index(fields=['cti_id'], name='dim_entity_cti_id_idx'), models.Index(fields=['sector'], name='dim_entity_sector_idx')],
            },
        ),
        migrations.CreateModel(
            name='BridgeCountry',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('member_value', models.TextField(blank=True, null=True)),
                ('member_count', models.IntegerField(blank=True, null=True)),
                ('weight_factor', models.FloatField(blank=True, null=True)),
                ('is_unknown_member', models.BooleanField(default=False)),
                ('country_group_key', models.CharField(max_length=32)),
                ('country', models.ForeignKey(db_column='country_id', on_delete=django.db.models.deletion.DO_NOTHING, related_name='report_links', to='warehouse.dimcountry')),
            ],
            options={
                'db_table': 'bridge_country',
                'constraints': [models.UniqueConstraint(fields=('country_group_key', 'country'), name='bridge_country_unique_member')],
            },
        ),
        migrations.CreateModel(
            name='BridgeEntity',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('member_value', models.TextField(blank=True, null=True)),
                ('member_count', models.IntegerField(blank=True, null=True)),
                ('weight_factor', models.FloatField(blank=True, null=True)),
                ('is_unknown_member', models.BooleanField(default=False)),
                ('entity_group_key', models.CharField(max_length=32)),
                ('entity', models.ForeignKey(db_column='entity_id', on_delete=django.db.models.deletion.DO_NOTHING, related_name='report_links', to='warehouse.dimentity')),
            ],
            options={
                'db_table': 'bridge_entity',
                'constraints': [models.UniqueConstraint(fields=('entity_group_key', 'entity'), name='bridge_entity_unique_member')],
            },
        ),
        migrations.CreateModel(
            name='BridgeGroup',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('member_value', models.TextField(blank=True, null=True)),
                ('member_count', models.IntegerField(blank=True, null=True)),
                ('weight_factor', models.FloatField(blank=True, null=True)),
                ('is_unknown_member', models.BooleanField(default=False)),
                ('group_group_key', models.CharField(max_length=32)),
                ('group', models.ForeignKey(db_column='group_id', on_delete=django.db.models.deletion.DO_NOTHING, related_name='report_links', to='warehouse.dimgroup')),
            ],
            options={
                'db_table': 'bridge_group',
                'constraints': [models.UniqueConstraint(fields=('group_group_key', 'group'), name='bridge_group_unique_member')],
            },
        ),
        migrations.CreateModel(
            name='FactReport',
            fields=[
                ('report_id', models.TextField(primary_key=True, serialize=False)),
                ('title', models.TextField(blank=True, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('actions', models.TextField(blank=True, null=True)),
                ('analysis', models.TextField(blank=True, null=True)),
                ('creation_date', models.DateField(blank=True, null=True)),
                ('publication_date', models.DateField(blank=True, null=True)),
                ('report_date', models.DateField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
                ('country_group_key', models.CharField(blank=True, max_length=32, null=True)),
                ('entity_group_key', models.CharField(blank=True, max_length=32, null=True)),
                ('group_group_key', models.CharField(blank=True, max_length=32, null=True)),
                ('classification', models.ForeignKey(db_column='classification_id', on_delete=django.db.models.deletion.DO_NOTHING, related_name='reports', to='warehouse.dimclassification')),
                ('evidence_type', models.ForeignKey(db_column='evidence_type_id', on_delete=django.db.models.deletion.DO_NOTHING, related_name='reports', to='warehouse.dimevidencetype')),
                ('importance_level', models.ForeignKey(db_column='importance_level_id', on_delete=django.db.models.deletion.DO_NOTHING, related_name='reports', to='warehouse.dimimportancelevel')),
                ('source', models.ForeignKey(db_column='source_id', on_delete=django.db.models.deletion.DO_NOTHING, related_name='reports', to='warehouse.dimsource')),
                ('threat_type', models.ForeignKey(db_column='threat_type_id', on_delete=django.db.models.deletion.DO_NOTHING, related_name='reports', to='warehouse.dimthreattype')),
            ],
            options={
                'verbose_name_plural': 'reports',
                'db_table': 'fact_report',
                'indexes': [models.Index(fields=['report_date'], name='fact_report_date_idx'), models.Index(fields=['country_group_key'], name='fact_country_key_idx'), models.Index(fields=['entity_group_key'], name='fact_entity_key_idx'), models.Index(fields=['group_group_key'], name='fact_group_key_idx')],
            },
        ),
    ]
