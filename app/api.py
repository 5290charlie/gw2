from flask import render_template, make_response, jsonify
from app import app
import os, sys

sys.path.append("%s/../src" % os.path.dirname(os.path.realpath(__file__)))

from models import *
import tools

@app.route('/api/favorite/<str:class_name>/<int:id>')
def favorite(class_name, id):
    response = {
        'success': false,
        'errors': []
    }

    try:
        obj = eval(class_name.capitalize()).get(id=id)
        response['success'] = true
    except:
        response['errors'].append("Error initializing class: '%s' with id: %d" % (class_name, id))

    return jsonify(response)
