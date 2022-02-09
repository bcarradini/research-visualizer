"""
Populate data models for the visualizer app. See help text for usage details.
"""
# Standard
import csv
import re

# 3rd Party
from django.core.management.base import BaseCommand

# Internal
from visualizer.models import ScopusClassification, ScopusSource
from visualizer.scopus_api import get_subject_area_classifications

# Constants
CSV_FILEPATH = './visualizer/static/data/scopus_sources.csv'
SOURCE_ID_COLUMN_NAME = 'Sourcerecord ID' # journal identifier within scopus
SOURCE_NAME_COLUMN_NAME = 'Source Title (Medline-sourced journals are indicated in Green)' # journal name
CLASSIFICATION_COLUMN_NAME = 'All Science Journal Classification Codes (ASJC)' # list of comma-separated classification codes

class Command(BaseCommand):
    help = ('''
        To use this script:
          1. Download the latest scopus source list from https://www.scopus.com, which will be an Excel spreadsheet.
          2. Convert the first tab of the spreadsheet (e.g. "Scopus Sources October 2021") to CSV format.
          3. Place CSV file in the `visualizer/static/data/scopus_sources.csv` directory of this project.
          4. Execute management script, `python manage.py populate_database.py`.
          5. If you encounter trouble parsing the script, make sure the constants defined at the top of this file 
          still align with the column names in the latest source list.
    ''')

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--execute',
            action='store_true',
            dest='execute',
            default=False,
            help='Actually alter database records',
        )

    def handle(self, *args, **kwargs):
        self.execute = kwargs.get('execute')
        self.preamble = f"populate_database: {'EXECUTE' if self.execute else 'TEST'}:"

        print(f"{self.preamble} begin")

        #
        # -- Create (or update) classifications
        #

        # TODO: comment
        _, classifications = get_subject_area_classifications()
        print(f"{self.preamble} update or create {len(classifications)} classifications")

        # TODO: comment
        if self.execute:
            for c in classifications:
                ScopusClassification.objects.update_or_create(code=c['code'], defaults={
                    'name': c['detail'],
                    'category_abbr': c['abbrev'],
                    'category_name': c['description'],
                })

        # TODO: comment
        with open(CSV_FILEPATH, 'r') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            rows = [row for row in csv_reader]

        # Separate header row from the rest of the rows, which describe the sources
        header_row = rows[0]
        source_rows = rows[1:]

        # Determine which columns hold the data we're interested in
        source_id_col_idx = header_row.index(SOURCE_ID_COLUMN_NAME)
        source_name_col_idx = header_row.index(SOURCE_NAME_COLUMN_NAME)
        classification_col_idx = header_row.index(CLASSIFICATION_COLUMN_NAME)

        # Count the sources
        num_sources = len(source_rows)
        print(f"{self.preamble} update or create {num_sources} sources")

        # Process each source
        for idx, row in enumerate(source_rows):
            source_id = row[source_id_col_idx]
            source_name = row[source_name_col_idx]
            classification_codes = row[classification_col_idx]

            # Create (or update) source object
            if self.execute:
                source, _ = ScopusSource.objects.update_or_create(source_id=source_id, defaults={'source_name': source_name})

            # Add classifications to sources
            codes = [code.strip() for code in re.split(',|;', classification_codes) if code.strip()]
            for code in codes:
                try:
                    source.classifications.add(ScopusClassification.objects.get(code=code))
                except Exception as exc:
                    print(f"ERROR: ")
                    print(f"ERROR: exc = {exc} ({source_id}, {source_name}, {code})")
                    print(f"ERROR: ")

            # Log progress
            if idx % 100 == 0:
                print(f"{self.preamble}     ... {idx} of {num_sources} ...")

        print(f"{self.preamble} end")

