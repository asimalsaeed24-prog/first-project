from django.db import models


class Dimension(models.Model):

    id = models.BigIntegerField(primary_key=True)

    class Meta:
        abstract = True


class DimRasdClassification(Dimension):
    classification_name = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "dim_rasd_classification"
        verbose_name_plural = "classifications"

    def __str__(self):
        return self.classification_name or "Unknown"


class DimRasdEvidenceType(Dimension):
    evidence_type_name = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "dim_rasd_evidence_type"
        verbose_name_plural = "evidence types"

    def __str__(self):
        return self.evidence_type_name or "Unknown"


class DimRasdImportanceLevel(Dimension):
    importance_level = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "dim_rasd_importance_level"
        verbose_name_plural = "importance levels"

    def __str__(self):
        return self.importance_level or "Unknown"


class DimRasdSource(Dimension):
    source_name = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "dim_rasd_source"
        verbose_name_plural = "sources"

    def __str__(self):
        return self.source_name or "Unknown"


class DimRasdThreatType(Dimension):
    threat_type_name = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "dim_rasd_threat_type"
        verbose_name_plural = "threat types"

    def __str__(self):
        return self.threat_type_name or "Unknown"


class DimCountry(Dimension):
    country_name = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "dim_country"
        verbose_name_plural = "countries"

    def __str__(self):
        return self.country_name or "Unknown"


class DimCtiAdversary(Dimension):
    adversary_id = models.TextField(null=True, blank=True)
    adversary_name = models.TextField(null=True, blank=True)
    country_group_key = models.CharField(max_length=32, null=True, blank=True)

    class Meta:
        db_table = "dim_cti_adversary"
        verbose_name_plural = "adversaries"

    def __str__(self):
        return self.adversary_name or self.adversary_id or "Unknown"


class DimRasdGroup(Dimension):
    group_name = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "dim_rasd_group"
        verbose_name_plural = "threat groups"

    def __str__(self):
        return self.group_name or "Unknown"


class DimRasdEntity(Dimension):
    cti_id = models.TextField(null=True, blank=True)
    prm_id = models.TextField(null=True, blank=True)
    entity_name_en = models.TextField(null=True, blank=True)
    entity_name_ar = models.TextField(null=True, blank=True)
    country = models.TextField(null=True, blank=True)
    category = models.TextField(null=True, blank=True)
    sector = models.TextField(null=True, blank=True)
    entity_type = models.TextField(null=True, blank=True)
    domain = models.TextField(null=True, blank=True)
    is_cti_entity = models.BooleanField(default=False)

    class Meta:
        db_table = "dim_rasd_entity"
        verbose_name_plural = "entities"
        indexes = [
            models.Index(fields=["cti_id"], name="dim_entity_cti_id_idx"),
            models.Index(fields=["sector"], name="dim_entity_sector_idx"),
        ]

    def __str__(self):
        return self.entity_name_en or self.entity_name_ar or "Unknown"


class FactRasdReport(models.Model):

    # Auto-generated surrogate key (from row_number() in SQL)
    id = models.BigIntegerField(primary_key=True)
    
    # Original natural key
    report_id = models.TextField(unique=True)

    title = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    actions = models.TextField(null=True, blank=True)
    analysis = models.TextField(null=True, blank=True)

    creation_date = models.DateField(null=True, blank=True)
    publication_date = models.DateField(null=True, blank=True)
    report_date = models.DateField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    classification = models.ForeignKey(
        DimRasdClassification, on_delete=models.DO_NOTHING,
        db_column="classification_id", related_name="reports",
    )
    evidence_type = models.ForeignKey(
        DimRasdEvidenceType, on_delete=models.DO_NOTHING,
        db_column="evidence_type_id", related_name="reports",
    )
    importance_level = models.ForeignKey(
        DimRasdImportanceLevel, on_delete=models.DO_NOTHING,
        db_column="importance_level_id", related_name="reports",
    )
    source = models.ForeignKey(
        DimRasdSource, on_delete=models.DO_NOTHING,
        db_column="source_id", related_name="reports",
    )
    threat_type = models.ForeignKey(
        DimRasdThreatType, on_delete=models.DO_NOTHING,
        db_column="threat_type_id", related_name="reports",
    )

    country_group_key = models.CharField(max_length=32, null=True, blank=True)
    entity_group_key = models.CharField(max_length=32, null=True, blank=True)
    group_group_key = models.CharField(max_length=32, null=True, blank=True)
    adversary_group_key = models.CharField(max_length=32, null=True, blank=True)

    class Meta:
        db_table = "fact_rasd_report"
        verbose_name_plural = "rasd reports"
        indexes = [
            models.Index(fields=["report_date"], name="fact_rasd_report_date_idx"),
            models.Index(fields=["country_group_key"], name="fact_rasd_country_key_idx"),
            models.Index(fields=["entity_group_key"], name="fact_rasd_entity_key_idx"),
            models.Index(fields=["group_group_key"], name="fact_rasd_group_key_idx"),
            models.Index(fields=["adversary_group_key"], name="fact_rasd_adversary_key_idx"),
            models.Index(fields=["report_id"], name="fact_rasd_report_id_idx"),
        ]

    def __str__(self):
        return self.title or self.report_id


class Bridge(models.Model):

    id = models.BigAutoField(primary_key=True)
    member_value = models.TextField(null=True, blank=True)
    member_count = models.IntegerField(null=True, blank=True)
    weight_factor = models.FloatField(null=True, blank=True)
    is_unknown_member = models.BooleanField(default=False)

    class Meta:
        abstract = True


class BridgeCountry(Bridge):
    country_group_key = models.CharField(max_length=32)
    country = models.ForeignKey(
        DimCountry, on_delete=models.DO_NOTHING,
        db_column="country_id", related_name="report_links",
    )

    class Meta:
        db_table = "bridge_country"
        constraints = [
            models.UniqueConstraint(
                fields=["country_group_key", "country"],
                name="bridge_country_unique_member",
            )
        ]


class BridgeEntity(Bridge):
    entity_group_key = models.CharField(max_length=32)
    entity = models.ForeignKey(
        DimRasdEntity, on_delete=models.DO_NOTHING,
        db_column="entity_id", related_name="report_links",
    )

    class Meta:
        db_table = "bridge_entity"
        constraints = [
            models.UniqueConstraint(
                fields=["entity_group_key", "entity"],
                name="bridge_entity_unique_member",
            )
        ]


class BridgeGroup(Bridge):
    group_group_key = models.CharField(max_length=32)
    group = models.ForeignKey(
        DimRasdGroup, on_delete=models.DO_NOTHING,
        db_column="group_id", related_name="report_links",
    )

    class Meta:
        db_table = "bridge_group"
        constraints = [
            models.UniqueConstraint(
                fields=["group_group_key", "group"],
                name="bridge_group_unique_member",
            )
        ]


class BridgeAdversary(Bridge):
    adversary_group_key = models.CharField(max_length=32)
    adversary = models.ForeignKey(
        DimCtiAdversary, on_delete=models.DO_NOTHING,
        db_column="adversary_dim_id", related_name="report_links",
    )

    class Meta:
        db_table = "bridge_adversary"
        constraints = [
            models.UniqueConstraint(
                fields=["adversary_group_key", "adversary"],
                name="bridge_adversary_unique_member",
            )
        ]


class BridgeAdversaryCountry(Bridge):
    """
    Bridge table linking adversaries to their target countries
    This is a direct relationship from CTI adversary data
    """
    country_group_key = models.CharField(max_length=32)
    adversary_id = models.TextField(null=True, blank=True)  # Natural key from CTI
    country = models.ForeignKey(
        DimCountry, on_delete=models.DO_NOTHING,
        db_column="country_id", related_name="adversary_links",
    )

    class Meta:
        db_table = "bridge_adversary_country"
        constraints = [
            models.UniqueConstraint(
                fields=["country_group_key", "country"],
                name="bridge_adversary_country_unique_member",
            )
        ]


class VwReport(models.Model):

    id = models.BigIntegerField(primary_key=True)
    report_id = models.TextField()
    title = models.TextField(null=True)
    description = models.TextField(null=True)
    actions = models.TextField(null=True)
    analysis = models.TextField(null=True)

    creation_date = models.DateField(null=True)
    publication_date = models.DateField(null=True)
    report_date = models.DateField(null=True)
    updated_at = models.DateTimeField(null=True)

    classification = models.TextField(null=True)
    evidence_type = models.TextField(null=True)
    importance = models.TextField(null=True)
    observation_source = models.TextField(null=True)
    threat_type = models.TextField(null=True)

    country_group_key = models.CharField(max_length=32, null=True)
    entity_group_key = models.CharField(max_length=32, null=True)
    group_group_key = models.CharField(max_length=32, null=True)
    adversary_group_key = models.CharField(max_length=32, null=True)

    class Meta:
        managed = False
        db_table = "vw_report"


class ReportMemberView(models.Model):

    report_id = models.TextField(primary_key=True)
    title = models.TextField(null=True)
    report_date = models.DateField(null=True)
    classification = models.TextField(null=True)
    importance = models.TextField(null=True)
    threat_type = models.TextField(null=True)
    weight_factor = models.FloatField(null=True)
    is_unknown_member = models.BooleanField(default=False)

    class Meta:
        abstract = True
        managed = False


class VwReportCountry(ReportMemberView):
    country_id = models.BigIntegerField(null=True)
    country_name = models.TextField(null=True)

    class Meta(ReportMemberView.Meta):
        managed = False
        db_table = "vw_report_country"


class VwReportGroup(ReportMemberView):
    group_id = models.BigIntegerField(null=True)
    group_name = models.TextField(null=True)

    class Meta(ReportMemberView.Meta):
        managed = False
        db_table = "vw_report_group"


class VwReportEntity(ReportMemberView):
    entity_id = models.BigIntegerField(null=True)
    entity_name_en = models.TextField(null=True)
    entity_name_ar = models.TextField(null=True)
    cti_id = models.TextField(null=True)
    prm_id = models.TextField(null=True)
    sector = models.TextField(null=True)
    category = models.TextField(null=True)
    entity_type = models.TextField(null=True)
    entity_country = models.TextField(null=True)
    is_cti_entity = models.BooleanField(default=False)

    class Meta(ReportMemberView.Meta):
        managed = False
        db_table = "vw_report_entity"


class VwReportAdversary(ReportMemberView):
    adversary_id = models.BigIntegerField(null=True)
    adversary_name = models.TextField(null=True)

    class Meta(ReportMemberView.Meta):
        managed = False
        db_table = "vw_report_adversary"


class VwAdversaryTargetCountry(models.Model):
    """
    Adversaries with their target countries
    Direct relationships from CTI adversary data
    """
    adversary_id = models.TextField(null=True, blank=True)
    adversary_name = models.TextField(null=True)
    country_group_key = models.CharField(max_length=32, null=True, blank=True)
    country_id = models.BigIntegerField(null=True)
    country_name = models.TextField(null=True)
    weight_factor = models.FloatField(null=True)
    is_unknown_member = models.BooleanField(default=False)
    total_targeted_countries = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = "vw_adversary_target_country"

    def __str__(self):
        return f"{self.adversary_name} → {self.country_name}"


class VwEntityCoverage(models.Model):

    metric = models.TextField(primary_key=True)
    value = models.BigIntegerField(null=True)

    class Meta:
        managed = False
        db_table = "vw_entity_coverage"

    def __str__(self):
        return f"{self.metric} = {self.value}"
