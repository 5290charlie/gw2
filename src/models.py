from peewee import *
from datetime import datetime, timedelta
from config import *

database = config.get('database')
hostname = config.get('hostname')
username = config.get('username')
password = config.get('password')

db = MySQLDatabase(database, host=hostname, user=username, passwd=password, threadlocals=True)

class BaseModel(Model):
    class Meta:
        database = db

class Region(BaseModel):
    name = CharField(index=True, unique=True)

    def get_worlds(self):
        return World.select().where(World.region==self)

class World(BaseModel):
    name = CharField(max_length=32, index=True, unique=True)
    region = ForeignKeyField(Region, index=True)

    def get_current_match(self):
        return Match.get_current().where(
            (Match.red_world == self) |
            (Match.blue_world == self) |
            (Match.green_world == self)
        ).get()

    def get_color(self):
        match = self.get_current_match()
        worlds = match.get_worlds()

        for color in worlds:
            if worlds[color] == self:
                return color

        return None

    def get_guilds(self):
        return Guild.select().where(Guild.world==self).order_by(Guild.name)

    @staticmethod
    def get_color_index(color):
        if color in world_colors:
            return world_colors.index(color)
        else:
            return 0

    @staticmethod
    def get_color_string(index):
        if index < len(world_colors):
            return world_colors[index]
        else:
            return world_colors[0]

class Map(BaseModel):
    type = CharField(index=True, unique=True)

class Match(BaseModel):
    wvw_match_id = CharField(index=True, max_length=3)
    red_world = ForeignKeyField(World, related_name='red_world', index=True)
    blue_world = ForeignKeyField(World, related_name='blue_world', index=True)
    green_world = ForeignKeyField(World, related_name='green_world', index=True)
    start_time = DateTimeField(index=True)
    end_time = DateTimeField(index=True)

    def is_current(self):
        now = datetime.utcnow()
        return (self.start_time <= now and self.end_time >= now)

    def get_worlds(self):
        return {
            'red': self.red_world,
            'blue': self.blue_world,
            'green': self.green_world
        }

    def get_scores(self):
        return Score.select().where(Score.match==self).order_by(Score.time)

    def get_ticks(self):
        return Tick.select().where(Tick.match==self).order_by(Tick.time)

    def get_name_for_map(self, map):
        color = map.type[:-4].lower()

        if color in world_colors:
            return "%s Borderlands" % self.get_worlds()[color].name
        else:
            return "Eternal Battlegrounds"

    @staticmethod
    def get_current():
        now = datetime.utcnow()
        return Match.select().where(Match.start_time <= now, Match.end_time >= now).order_by(Match.wvw_match_id)

class Objective(BaseModel):
    map = ForeignKeyField(Map, index=True, null=True)
    name = CharField(max_length=32, index=True)
    points = IntegerField(default=0, index=True)

class Guild(BaseModel):
    guild_key = CharField(max_length=36, index=True, unique=True)
    tag = CharField(max_length=16, index=True)
    name = CharField(index=True)
    world = ForeignKeyField(World, index=True)

    def get_claims(self):
        return Claim.select().where(Claim.guild==self).order_by(-Claim.updated)

    def get_migrations(self):
        return Migration.select().where(Migration.guild==self).order_by(-Migration.updated)

class Emblem(BaseModel):
    data = TextField(default='{}')
    guild = ForeignKeyField(Guild, index=True, unique=True)
    updated = DateTimeField(default=datetime.utcnow, index=True)

class Migration(BaseModel):
    guild = ForeignKeyField(Guild)
    world = ForeignKeyField(World)
    updated = DateTimeField(default=datetime.utcnow)

class Claim(BaseModel):
    guild = ForeignKeyField(Guild)
    match = ForeignKeyField(Match)
    objective = ForeignKeyField(Objective)
    duration = IntegerField(default=0)
    updated = DateTimeField(default=datetime.utcnow)

    def get_map_name(self):
        return self.match.get_name_for_map(self.objective.map)

class Score(BaseModel):
    match = ForeignKeyField(Match)
    world = ForeignKeyField(World)
    score = IntegerField(default=0)
    time = DateTimeField(default=datetime.utcnow)

class Tick(BaseModel):
    match = ForeignKeyField(Match)
    world = ForeignKeyField(World)
    points = IntegerField(default=0)
    time = DateTimeField(default=datetime.utcnow)

class MatchNotCurrent(Exception):
    pass
