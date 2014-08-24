import os
import sys

path = 'C:\\projects\\metobs_service\\service\\metservice'
if path not in sys.path:
    sys.path.append(path)
	
os.environ['DJANGO_SETTINGS_MODULE'] = 'metservice.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
