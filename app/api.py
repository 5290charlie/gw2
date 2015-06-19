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

@app.route('/api/favorite/<action>/<class_name>/<int:id>')
def favorite(class_name, action, id):
    fav_cookie = request.cookies.get('favorites')

    if fav_cookie:
        favorites = json.loads(fav_cookie)
    else:
        favorites = {}

    try:
        obj = eval(class_name.capitalize()).get(id=id)

        if action == 'remove':
            if class_name in favorites and id in favorites[class_name]:
                favorites[class_name].remove(id)
                response['success'] = True
            else:
                response['errors'].append("Class: '%s' or %s id: %d not in favorites list!" % (class_name, class_name, id))
        else:
            if class_name not in favorites:
                favorites[class_name] = []

            if id not in favorites[class_name]:
                favorites[class_name].append(id)
                response['success'] = True
            else:
                response['errors'].append("Already favorited %s %d" % (class_name, id))

        response['favorites'] = favorites
    except:
        response['errors'].append("Error initializing class: '%s' with id: %d" % (class_name, id))

    resp = jsonify(response)

    if response['success']:
        resp.set_cookie('favorites', json.dumps(favorites))

    return resp
