#!/usr/bin/python3
import sys
sys.path.insert(0, '/var/www/html/Mobile_Sales')
sys.path.insert(0, '/var/www/html/Mobile_Sales/venv/lib/python3.13/site-packages')

from app import create_app
application = create_app()