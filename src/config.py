import ConfigParser

class gw2Config:
    config = None
    options = {}
    bool_values = {
        'verbose': ['true', 'yes', 't', 'y', '1']
    }

    def __init__(self, inifile='/vagrant/python/gw2/settings.ini'):
        self.config = ConfigParser.ConfigParser()
        self.config.read(inifile)

        for section in self.config.sections():
            for option in self.config.options(section):
                self.options[option] = self.config.get(section, option)

    def get(self, option):
        option = option.lower()

        if option in self.bool_values:
            return self.options[option].lower() in self.bool_values[option]
        elif option in self.options:
            return self.options[option]
        else:
            return False

config = gw2Config()

objective_points = {
    'castle': 35,
    'keep': 25,
    'tower': 10,
    'camp': 5
}

world_colors = [
    'red',
    'blue',
    'green'
]