from flask import render_template
from app import app
import os, sys

sys.path.append("%s/../src" % os.path.dirname(os.path.realpath(__file__)))

from models import *
import tools

@app.route('/')
@app.route('/index')
def index():
    matches = tools.get_current_matches()
    return render_template('index.html',
                           matches=matches)

@app.route('/match/<int:match_id>')
def match(match_id):
    match = Match.get(id=match_id)
    return render_template('match.html',
                           match=match)

@app.route('/world/<int:world_id>')
def world(world_id):
    world = World.get(id=world_id)
    guilds = Guild.select().where(Guild.world==world)
    return render_template('world.html',
                           world=world,
                           guilds=guilds)

@app.route('/guild/<int:guild_id>')
def guild(guild_id):
    guild = Guild.get(id=guild_id)
    claims = Claim.select().where(Claim.guild==guild)
    return render_template('guild.html',
                           guild=guild,
                           claims=claims)