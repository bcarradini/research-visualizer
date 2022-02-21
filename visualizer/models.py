"""
Data models for the visualizer app.

IMPORTANT:
To populate these data models, use the management command `populate_database.py`
"""
# 3rd party
from django.db import models
from django.contrib.postgres.fields import jsonb
from django.core.exceptions import ValidationError
from django_extensions.db.models import TimeStampedModel


#
# -- Scopus Subjects & Sources
#


class ScopusClassification(TimeStampedModel):
    # Classification; e.g. 1602, "Analytical Chemistry"
    code = models.CharField(max_length=8)
    name = models.CharField(max_length=64)

    # Category; e.g. "CHEM", "Chemistry"
    category_abbr = models.CharField(max_length=4)
    category_name = models.CharField(max_length=64)

    # TODO: unique constraint: code

    def __str__(self):
        return f"{self.name} ({self.category_abbr})"


class ScopusSource(TimeStampedModel):
    # Journal (or other publication)
    source_id = models.BigIntegerField()
    source_name = models.CharField(max_length=512)
    p_issn = models.CharField(max_length=8, blank=True, null=True)
    e_issn = models.CharField(max_length=8, blank=True, null=True)

    # Classification codes; the same source may be assigned to multiple classifications    
    classifications = models.ManyToManyField(ScopusClassification, db_index=True, related_name='sources')

    # TODO: unique constraint: source_id

    def __str__(self):
        return f"{self.source_name} ({self.source_id})"


#
# -- Search Results
#


class Search(TimeStampedModel):
    # Executed search
    query = models.TextField()
    context = jsonb.JSONField(default=dict) # e.g. {'categories': ['MULT','AGRI','CHEM']}

    # Queued job used to execute search
    finished = models.BooleanField(default=False)

    #
    # -- Superclass methods
    #

    def save(self, *args, **kwargs):
        # Raise exception is categories is missing from context
        categories = self.context.get('categories')
        if categories is None or type(categories) is not list:
            raise ValidationError(f"context['categories'] must be a list")

        # Initialize `finished_categories` in context if it is missing
        finished_categories = self.context.get('finished_categories')
        if finished_categories is None or type(finished_categories) is not list:
            self.context['finished_categories'] = []

        # Invoke save() method from superclass
        return super(Demographics, self).save(*args, **kwargs)

    #
    # -- Custom methods
    #

    @classmethod
    def _init_search(cls, query, categories):
        return cls.objects.create(query=query, context=Search._init_context(categories))

    @staticmethod
    def _init_context(categories):
        return {'categories': categories, 'finished_categories': []}


class SearchResult_Category(TimeStampedModel):
    # Executed search
    search = models.ForeignKey(Search, related_name='categories', on_delete=models.CASCADE)

    # Category; e.g. "CHEM"
    category_abbr = models.CharField(max_length=4)

    # Count of search result entries across classifications within category, e.g.:
    #   {
    #     '1600': {"name": "Chemistry (all)", count: 100},             // 100 entries for classification 1600
    #     '1601': {"name": "Chemistry (miscellaneous)", count: 200},   // 200 entries for classification 1601
    #     ...
    #     '1607': {"name": "Spectroscopy", count: 300},                // 300 entries for classification 1607
    #     'unknown': {"name": "Unknown", count: 100},                  // 100 entries with unknown classification
    #     'total': {"name": "Total", count: 1510},                     // 1500 entries for entire category
    #   }
    counts = jsonb.JSONField(default=dict)

    # TODO: unique constraint: search + category_abbr

class SearchResult_Entry(models.Model):
    # Executed search
    search = models.ForeignKey(Search, related_name='entries', on_delete=models.CASCADE)

    # Category; e.g. "CHEM"
    category_abbr = models.CharField(max_length=4, db_index=True)

    # Entry
    scopus_id = models.CharField(max_length=16)
    title = models.TextField()
    first_author = models.CharField(max_length=128, blank=True, null=True)
    document_type = models.CharField(max_length=2, blank=True, null=True)

    # Entry publication
    publication_name = models.TextField()
    scopus_source = models.ForeignKey(ScopusSource, blank=True, null=True, related_name='entries', on_delete=models.CASCADE)
