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
from visualizer.scopus import get_subject_area_classifications

from argparse import RawTextHelpFormatter

# Constants
CSV_FILEPATH = './visualizer/static/data/scopus_sources.csv'
SOURCE_ID_COLUMN_NAME = 'Sourcerecord ID' # journal identifier within scopus
SOURCE_NAME_COLUMN_NAME = 'Source Title (Medline-sourced journals are indicated in Green)' # journal name
P_ISSN_COLUMN_NAME = 'Print-ISSN'
E_ISSN_COLUMN_NAME = 'E-ISSN'
CLASSIFICATION_COLUMN_NAME = 'All Science Journal Classification Codes (ASJC)' # list of comma-separated classification codes

class Command(BaseCommand):
    help = '''
How To:
  1. Download the latest scopus source list from https://www.scopus.com, which will be an Excel spreadsheet.
  2. Convert the first tab of the spreadsheet (e.g. "Scopus Sources October 2021") to CSV format.
  3. Place CSV file at `visualizer/static/data/scopus_sources.csv` within this source code repository.
  4. Execute this script: `python manage.py populate_database --execute`.
  5. If the script cannot parse the CSV file:
      a. Make sure the constants defined at the top of this file still align with the column names in the latest source list.
      b. Make sure the `encoding` specified when opening the CSV file aligns with how the CSV file was generated (utf-8? utf-8-sig? etc).
    '''

    def create_parser(self, * args, ** kwargs):
        parser = super(Command, self).create_parser( * args, ** kwargs)
        parser.formatter_class = RawTextHelpFormatter # respect line breaks in help text
        return parser

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

        # Fetch current subject area classifications from Scopus
        _, classifications = get_subject_area_classifications()
        print(f"{self.preamble} update or create {len(classifications)} classifications")

        # Update or create internal classification records to align with current Scopus data
        if self.execute:
            for _, c in classifications.items():
                ScopusClassification.objects.update_or_create(code=c['code'], defaults={
                    'name': c['name'],
                    'category_abbr': c['category_abbr'],
                    'category_name': c['category_name'],
                })

        # Open CSV file of sources and read it in, row-by-row
        with open(CSV_FILEPATH, 'r', encoding='utf-8-sig') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            rows = [row for row in csv_reader]

        # Separate header row from the rest of the rows, which describe the sources
        header_row = rows[0]
        source_rows = rows[1:]
        print(f"{self.preamble} header_row = {header_row}")

        # Determine which columns hold the data we're interested in
        source_id_col_idx = header_row.index(SOURCE_ID_COLUMN_NAME)
        source_name_col_idx = header_row.index(SOURCE_NAME_COLUMN_NAME)
        p_issn_col_idx = header_row.index(P_ISSN_COLUMN_NAME)
        e_issn_col_idx = header_row.index(E_ISSN_COLUMN_NAME)
        classification_col_idx = header_row.index(CLASSIFICATION_COLUMN_NAME)

        # Count the sources
        num_sources = len(source_rows)
        print(f"{self.preamble} update or create {num_sources} sources")

        # Process each source
        for idx, row in enumerate(source_rows):
            source_id = row[source_id_col_idx] or None
            source_name = row[source_name_col_idx] or None
            p_issn = row[p_issn_col_idx] or None
            e_issn = row[e_issn_col_idx] or None
            classification_codes = row[classification_col_idx] or ''

            # Create (or update) source object
            if self.execute:
                source, _ = ScopusSource.objects.update_or_create(source_id=source_id, defaults={
                    'source_name': source_name,
                    'p_issn': p_issn,
                    'e_issn': e_issn,
                })

            # Add classifications to sources
            codes = [code.strip() for code in re.split(',|;', classification_codes) if code.strip()]
            if self.execute:
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
