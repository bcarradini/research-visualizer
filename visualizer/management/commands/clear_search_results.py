"""
Populate data models for the visualizer app. See help text for usage details.
"""
# Standard

# 3rd Party
from django.core.management.base import BaseCommand

# Internal

class Command(BaseCommand):
    help = ('''
        To use this script:
          1. TODO
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
        self.preamble = f"clear_search_results: {'EXECUTE' if self.execute else 'TEST'}:"

        print(f"{self.preamble} begin")

        # TODO: Implement this script!

        print(f"{self.preamble} end")
