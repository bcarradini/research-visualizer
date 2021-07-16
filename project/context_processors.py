
# 3rd party 
from django.conf import settings

def project_settings(request):
    # Return dictionary of projects settings to include in template context
    return {k:getattr(settings,k) for k in settings.CONTEXT_SETTINGS}
