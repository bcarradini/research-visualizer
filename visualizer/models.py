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

# Internal
from project.worker import dequeue_job

# Constants
CATEGORIES = 'categories'
FINISHED_CATEGORIES = 'finished_categories'
NEXT_CATEGORY = 'next_category'
NEXT_CURSOR = 'next_cursor'


#
# -- Scopus Subjects & Sources
#


class ScopusClassification(TimeStampedModel):
    UNKNOWN = 'unknown'

    # Classification; e.g. 1602, "Analytical Chemistry"
    code = models.CharField(max_length=8)
    name = models.CharField(max_length=64)

    # Category; e.g. "CHEM", "Chemistry"
    category_abbr = models.CharField(max_length=4)
    category_name = models.CharField(max_length=64)

    class Meta(object):
        unique_together = [('code')]

    def __str__(self):
        return f"{self.name} ({self.category_abbr})"

    @classmethod
    def all_categories(cls):
        return list(ScopusClassification.objects.distinct('category_abbr').values_list('category_abbr', flat=True))


class ScopusSource(TimeStampedModel):
    # Journal (or other publication)
    source_id = models.BigIntegerField()
    source_name = models.CharField(max_length=512)
    p_issn = models.CharField(max_length=8, blank=True, null=True)
    e_issn = models.CharField(max_length=8, blank=True, null=True)

    # Classification codes; the same source may be assigned to multiple classifications    
    classifications = models.ManyToManyField(ScopusClassification, db_index=True, related_name='sources')

    class Meta(object):
        unique_together = [('source_id')]

    def __str__(self):
        return f"{self.source_name} ({self.source_id})"


#
# -- Search Results
#


class Search(TimeStampedModel):
    BOOLEAN_OPERATORS = ['AND', 'OR'] # supported boolean operators that may be embedded in the search query; case-sensitive

    # The search query
    query = models.TextField()

    # The search context
    context = jsonb.JSONField(default=dict) # e.g. {'categories': ['MULT','AGRI','CHEM']}

    # Status of the search
    finished = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)

    # Job queued for RQ worker that will perform the search (e.g. '58e50bb9-4b26-4596-af90-791df9ea41c0')
    job_id = models.CharField(max_length=64, blank=True, null=True)

    #
    # -- Superclass methods
    #

    def save(self, *args, **kwargs):
        # Set finished flag if the set of categories matches the set of finished categories
        if set(self.context[CATEGORIES]) == set(self.context[FINISHED_CATEGORIES]):
            self.finished = True
        else:
            self.finished = False

        # Invoke superclass method
        return super().save(*args, **kwargs)

    #
    # -- Custom methods
    #

    @classmethod
    def init_search(cls, query, categories=None):
        # Create instance of class with query and context initialized
        return cls.objects.create(query=query, context=Search._init_context(categories))

    @classmethod
    def delete_search(cls, search_id):
        """Mark the search identified by ID as deleted; cancel any related job."""
        search = Search.objects.filter(id=search_id).first()
        if search:
            # Cancel any related job
            dequeue_job(search.job_id)
            # Mark as deleted
            search.deleted = True
            search.job_id = None
            search.save()

    @classmethod
    def _init_context(cls, categories=None):
        # If no categories were specified, default to all categories
        categories = categories or ScopusClassification.all_categories()
        # Return initialize context
        return {CATEGORIES: categories, FINISHED_CATEGORIES: [], NEXT_CATEGORY: None, NEXT_CURSOR: None}

    def set_next_cursor(self, category, cursor):
        self.context.update({NEXT_CATEGORY: category, NEXT_CURSOR: cursor})
        self.save()

    @property
    def scopus_query(self):
        """TODO: comment"""
        return self._scopus_query(self.query)

    @classmethod
    def _scopus_query(cls, query):
        """TODO: comment

        References:
        https://dev.elsevier.com/sc_search_tips.html
        """
        scopus_query = query

        for operator in cls.BOOLEAN_OPERATORS:
            scopus_query = f'" {operator} "'.join(scopus_query.split(f' {operator} '))

        return f'"{scopus_query}"'


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

    class Meta(object):
        unique_together = [('search', 'category_abbr')]
    

class SearchResult_Entry(models.Model):
    # Executed search
    search = models.ForeignKey(Search, related_name='entries', on_delete=models.CASCADE)

    # Category; e.g. "CHEM"
    category_abbr = models.CharField(max_length=4, db_index=True)

    # Entry
    scopus_id = models.CharField(max_length=16)
    doi = models.CharField(max_length=256, blank=True, null=True)
    title = models.TextField()
    first_author = models.CharField(max_length=128, blank=True, null=True)
    document_type = models.CharField(max_length=2, blank=True, null=True)

    # Entry publication
    publication_name = models.TextField(blank=True, null=True)
    scopus_source = models.ForeignKey(ScopusSource, blank=True, null=True, related_name='entries', on_delete=models.CASCADE)

    class Meta(object):
        unique_together = [('search', 'category_abbr', 'scopus_id')]

