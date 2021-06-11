"""
WSGI config for project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import os
print('%s: init' % __name__)
print('%s:     ENVIRONMENT=%s' % (__name__, os.environ.get('ENVIRONMENT')))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
