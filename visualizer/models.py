"""
Data models for the visualizer app.

IMPORTANT:
To populate these data models, use the management command `populate_database.py`
"""
# 3rd party
from django.db import models
from django_extensions.db.models import TimeStampedModel

#
# -- Scopus Subjects & Sources
#

class ScopusClassification(TimeStampedModel):
    # E.g. 1602, "Analytical Chemistry"
    code = models.CharField(max_length=8)
    name = models.CharField(max_length=64)


class ScopusSource(TimeStampedModel):
    # A journal
    source_id = models.BigIntegerField()
    source_name = models.CharField(max_length=512)

    # Classification codes; the same source may be assigned to multiple classifications    
    classifications = models.ManyToManyField(ScopusClassification, db_index=True, related_name='sources')
