from flask import render_template, make_response
from app import app
import os, sys

sys.path.append("%s/../src" % os.path.dirname(os.path.realpath(__file__)))

from models import *
import tools

@app.template_global()
def active_pages():
    return [
        'matches',
        'worlds',
        'guilds',
        'emblems'
    ]

@app.route('/')
@app.route('/index')
def index():
    matches = Match.get_current()
    resp = make_response(render_template('index.html', **locals()))
    resp.set_cookie('Test_Cookie', 'This is a cookie value')
    return resp

@app.route('/matches')
@app.route('/matches/<int:match_id>')
def matches(match_id=None):
    if match_id is not None:
        match = Match.get(Match.id==match_id)
    else:
        match = None
        matches = Match.get_current()

    return render_template('matches.html', **locals())

@app.route('/worlds')
@app.route('/worlds/<int:world_id>')
def worlds(world_id=None):
    if world_id is not None:
        world = World.get(World.id==world_id)
    else:
        world = None
        worlds = World.select()

    resp = make_response(render_template('worlds.html', **locals()))

    if world is not None:
        resp.set_cookie('World_visited', world.name)

    return resp

@app.route('/guilds')
@app.route('/guilds/<int:guild_id>')
def guilds(guild_id=None):
    if guild_id is not None:
        guild = Guild.get(Guild.id==guild_id)
    else:
        guild = None
        guilds = Guild.select()

    return render_template('guilds.html', **locals())

@app.route('/emblems')
@app.route('/emblems/<int:emblem_id>')
def emblems(emblem_id=None):
    if emblem_id is not None:
        emblem = Emblem.get(Emblem.id==emblem_id)
    else:
        emblem = None
        emblems = Emblem.select()

    return render_template('emblems.html', **locals())
