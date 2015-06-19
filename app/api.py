from flask import request, render_template, make_response, jsonify
from app import app
import os, sys, json

sys.path.append("%s/../src" % os.path.dirname(os.path.realpath(__file__)))

from models import *
import tools

response = {
    'success': False,
    'errors': []
}

cookie_expiration = datetime.utcnow() + timedelta(days=config.get('cookie_life'))

def bake_cookie(response, key, value):
    response.set_cookie(key, value, expires=cookie_expiration)

@app.route('/api/favorite/<class_name>/<int:id>')
def favorite(class_name, id):
    fav_cookie = request.cookies.get('favorites')

    if fav_cookie:
        favorites = json.loads(fav_cookie)
    else:
        favorites = {}

    try:
        obj = eval(class_name.capitalize()).get(id=id)

        if class_name not in favorites:
            favorites[class_name] = []

        favorites[class_name].append(id)

        response['success'] = True
    except:
        response['errors'].append("Error initializing class: '%s' with id: %d" % (class_name, id))

    resp = jsonify(response)

    if response['success']:
        resp.set_cookie('favorites', json.dumps(favorites))
        # bake_cookie(resp, 'favorites', json.dumps(favorites))

    return resp
