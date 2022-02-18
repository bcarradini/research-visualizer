#!/usr/bin/env python
"""
An RQ worker to execute queued jobs.

References:
https://python-rq.org/
https://devcenter.heroku.com/articles/python-rq
"""
# Standard
import os
import sys

# 3rd party
import django

# --------------------------------------------------------------------------------------------------
# Setup worker as standalone Django App
# --------------------------------------------------------------------------------------------------
# Designate settings module
#     https://docs.djangoproject.com/en/1.11/topics/settings/#designating-the-settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
# Ensure project root is in import search path so that project.settings can be found
#     https://diveintopython3.net/your-first-python-program.html#importsearchpath
sys.path.insert(0, os.path.abspath(''))
# Populate Django's application registery
#     https://docs.djangoproject.com/en/3.0/topics/settings/#calling-django-setup-is-required-for-standalone-django-usage
django.setup()
# --------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    from project.worker import worker
    worker()
