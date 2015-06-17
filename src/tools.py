import api, json, logging, multiprocessing
from syslog import syslog
from models import *

verbose = config.get('verbose')

logging.basicConfig(filename='/var/log/syslog', level=logging.WARNING)

def log(msg, override=False):
    if verbose or override:
        syslog("[%s]: %s" % (multiprocessing.current_process(), msg))

def init():
    models = [Region, World, Map, Match, Objective, Guild, Emblem, Migration, Claim, Score, Tick]
    db.create_tables(models, True)

    table_indexes = {
        'match': ['wvw_match_id', 'start_time', 'end_time'],
        'migration': ['guild', 'world']
    }

    for table in table_indexes:
        columns = table_indexes[table]
        indexes = db.get_indexes(table)
        index_name = '_'.join(columns)
        class_name = table.capitalize()
        has_index = False

        for i in indexes:
            if all(col in i.name for col in columns):
                has_index = True
                break

        if has_index:
            log("Found index: '%s' for table: %s" % (index_name, table))
        else:
            log("Index: '%s' not found for table: %s, creating it..." % (index_name, table))
            db.create_index(eval(class_name), columns, True)

    regions = {
        '1': Region.get_or_create(name='na')[0],
        '2': Region.get_or_create(name='eu')[0]
    }

    for info in api.get_world_names():
        zone = info['id'][:1]
        region = regions[zone]
        world, created = World.get_or_create(id=info['id'], name=info['name'], region=region)

        if created:
            log("Created world: %s with id: %d in region: %s" % (world.name, world.id, world.region.name))
        else:
            log("World: %s already exists!" % world.name)

    for info in api.get_wvw_objective_names():
        name = info['name']
        points = 0

        if name[0:2] != '((':
            if name.lower() in objective_points:
                points = objective_points[name.lower()]
            else:
                points = objective_points['camp']
        objective, created = Objective.get_or_create(id=info['id'], name=name, points=points)

        if created:
            log("Created objective: %s with id: %d worth %d points" % (objective.name, objective.id, objective.points))
        else:
            log("Objective: %s[%d] already exists!" % (objective.name, objective.id))

def sync():
    matches = api.get_wvw_matches()['wvw_matches']

    for match_info in matches:
        wvw_match_id = match_info['wvw_match_id']
        red = World.get(id=match_info['red_world_id'])
        blue = World.get(id=match_info['blue_world_id'])
        green = World.get(id=match_info['green_world_id'])
        start_time = match_info['start_time'].replace('T', ' ').replace('Z', '')
        end_time = match_info['end_time'].replace('T', ' ').replace('Z', '')

        match, created = Match.get_or_create(wvw_match_id=wvw_match_id, red_world=red, blue_world=blue, green_world=green, start_time=start_time, end_time=end_time)

        if created:
            log("Inserted match: (%s, %d, %d, %d, %s, %s)" % (wvw_match_id, red.id, blue.id, green.id, start_time, end_time))

def mine_match(match):
    try:
        log("Mining match: '%s'" % match.wvw_match_id)
        now = datetime.utcnow()

        db.connect()

        objectives = {}

        for o in Objective.select():
            objectives[o.id] = o

        match_details = api.get_wvw_match_details(match.wvw_match_id)

        worlds = {
            'red': match.red_world,
            'blue': match.blue_world,
            'green': match.green_world
        }

        ticks = {
            'red': 0,
            'blue': 0,
            'green': 0
        }

        log("Match: '%s' - Red='%s', Blue='%s', Green='%s'\n" % (match.wvw_match_id, match.red_world.name, match.blue_world.name, match.green_world.name))

        if 'scores' in match_details:
            for score in match_details['scores']:
                index = match_details['scores'].index(score)
                color = World.get_color_string(index)
                world = worlds[color]

                try:
                    Score.get(Score.match == match, Score.world == world, Score.time > (now - timedelta(minutes=15)))
                except Score.DoesNotExist:
                    Score.create(match=match, world=world, score=score)

        if 'maps' in match_details:
            log("Processing maps for match '%s'" % match.wvw_match_id)

            for map_details in match_details['maps']:
                map_type = map_details['type']
                map, created = Map.get_or_create(type=map_type)

                log("Processing map: %s for match '%s'" % (map_type, match.wvw_match_id))

                if created:
                    log("Created map %s" % map_type)

                for objective_details in map_details['objectives']:
                    world_color = objective_details['owner'].lower()

                    if objective_details['id'] not in objectives:
                        log("Unknown objective! %s[%d]" % (objective_details, objective_details['id']), True)
                        return

                    objective = objectives[objective_details['id']]

                    objective_name = objective.name.encode('utf-8')

                    log("Processing objective %s[%d] for match '%s'" % (objective_name, objective_details['id'], match.wvw_match_id))

                    if world_color in worlds:
                        world = worlds[world_color]

                        if world_color in ticks:
                            ticks[world_color] += objective.points
                    else:
                        world = None

                    if world is not None and 'owner_guild' in objective_details:
                        world_name = world.name.encode('utf-8')
                        guild_key = objective_details['owner_guild']

                        log("Objective %s owned by guild: %s with world: %s" % (objective_name, guild_key, world_name))

                        log("Getting details for guild: %s" % guild_key)
                        guild_details = api.get_guild_details(guild_key)

                        guild_tag = guild_details['tag'].encode('utf-8')
                        guild_name = guild_details['guild_name'].encode('utf-8')

                        try:
                            guild = Guild.get(guild_key=guild_key)

                            if guild.world != world:
                                guild.world = world
                                log("Updating guild: %s world to: %s" % (guild_name, world_name))
                                guild.save()
                        except Guild.DoesNotExist:
                            log("Guild [%s]%s does not exist, creating it..." % (guild_tag, guild_name))
                            guild = Guild.create(guild_key=guild_key, name=guild_name, tag=guild_tag, world=world)

                        migration, created = Migration.get_or_create(guild=guild, world=world)

                        if created:
                            log("Tracked new migration for guild '%s' with world: '%s'" % (guild_name, world_name))
                        else:
                            migration.updated = now
                            migration.save()
                            log("Guild: '%s' association with world: '%s' has been updated" % (guild_name, world_name))

                        emblem, created = Emblem.get_or_create(guild=guild)

                        if 'emblem' in guild_details:
                            if created:
                                log("Created emblem for guild [%s]%s" % (guild_tag, guild_name))

                            diff = now - emblem.updated

                            if diff.days > 0 or emblem.data == '{}':
                                emblem.data = json.dumps(guild_details['emblem'])
                                emblem.updated = datetime.utcnow()
                                emblem.save()
                                log("Updated emblem data for guild: %s" % guild_name)

                        try:
                            threshold = now - timedelta(minutes=5)
                            claim = Claim.get(Claim.guild == guild, Claim.match == match, Claim.objective == objective, Claim.map == map, Claim.updated > threshold)
                            claim_diff = now - claim.updated
                            claim.duration += claim_diff.seconds
                            claim.updated = now
                            claim.save()
                            log("Guild: %s continues to claim[%d] objective: %s" % (guild_name, claim.id, objective_name))
                        except Claim.DoesNotExist:
                            claim = Claim.create(guild=guild, match=match, objective=objective, map=map)
                            log("Tracked new claim[%d] guild=%s claimed objective=%s" % (claim.id, guild_name, objective_name))

        for color in ticks:
            tick = ticks[color]
            world = worlds[color]

            try:
                Tick.get(Tick.match == match, Tick.world == world, Tick.time > (now - timedelta(minutes=15)))
            except Tick.DoesNotExist:
                Tick.create(match=match, world=world, points=tick)

        if not db.is_closed():
            log("Closing DB")
            db.close()
            log("DB closed")

    except:
        log("EXCEPTION CAUGHT IN MINING FUNCTION (THREAD)")
        logging.exception("Exception mining match!")
        raise

def get_current_matches():
    date_now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    return Match.select().where(Match.start_time <= date_now, Match.end_time >= date_now)