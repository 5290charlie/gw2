import logging, urllib3, json
from syslog import syslog

http = urllib3.PoolManager()

def get_items():
    """ Get a list of all item ids. """
    return _request("items.json")

def get_item_details(id, lang="en"):
    """ Get details of specific item. """
    return _request("item_details.json", item_id=id, lang=lang)

def get_recipes():
    """ Get a list of all recipes. """
    return _request("recipes.json")

def get_recipe_details(id, lang="en"):
    """ Get details of specific item. """
    return _request("recipe_details.json", recipe_id=id, lang=lang)

def get_wvw_matches():
    """ Get the current running WvW matches. """
    return _request("wvw/matches.json")

def get_wvw_match_details(id):
    """ Get the current match details. """
    return _request("wvw/match_details.json", match_id=id)

def get_wvw_objective_names(lang="en"):
    """ Get the names of all objectives in WvW maps. """
    return _request("wvw/objective_names.json", lang=lang)

def get_guild_details(id):
    """ GET details for specified guild """
    return _request("guild_details.json", guild_id=id)

def get_event_names(lang="en"):
    """ Get names of all existing events. """
    return _request("event_names.json", lang=lang)

def get_map_names(lang="en"):
    """ Get names of all maps. """
    return _request("map_names.json", lang=lang)

def get_world_names(lang="en"):
    """ Get names of all world servers. """
    return _request("world_names.json", lang=lang)

def get_events(**args):
    """ Get list events based on filtering by world, map and event. """
    return _request("events.json", **args)

def _request(json_location, **args):
    """ Makes a request on the Guild Wars 2 API."""
    url = 'https://api.guildwars2.com/v1/' + json_location + '?' + '&'.join(str(argument) + '=' + str(value) for argument, value in args.items())

    try:
        response = http.request('GET', url)

        if response.status == 200:
            return json.loads(response.data)
        else:
            syslog("Unknown issue with GW2 API request! Attemplted URL='%s', recieved status=%d" % (url, response.status))
            return {}
    except:
        syslog("Exception raised (assuming timeout) with URL='%s'" % url)
        logging.exception("Exception making GW2 API request!")
        raise
