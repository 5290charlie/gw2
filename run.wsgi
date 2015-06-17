#!/usr/bin/python
import os, sys, logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,os.path.dirname(os.path.realpath(__file__)))

from app import app as application
from src.config import *
application.secret_key = config.get('secret_key')