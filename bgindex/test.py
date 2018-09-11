#!/home/carl/.pyvenv3/bin/python
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bgindex.settings')
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
import bgs.models
