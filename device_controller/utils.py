import json
from pathlib import Path

class Config(object):
    config = None
    reload = False

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Config, cls).__new__(cls)
        return cls.instance

    def getConfig(self):
        # TODO accommodate remote update of config values to force reload
        if self.config == None or self.reload:
            configfile = Path(__file__).with_name("config.json")
            with configfile.open("r") as configreader:
                self.config = json.loads(configreader.read())
        return self.config

if __name__ == '__main__':
    config = Config()
    other_config = Config()
    print(config is other_config)
    print(config.getConfig() == other_config.getConfig())
    print(other_config.getConfig())