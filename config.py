import configparser
import os
import sys

# Constants for default values to be written to a local config file if
# one does not exist.
HOST = 'localhost' # More human-freindly than the ip address; replaced below
PORT = 8042
LOGFILEPATH = './log'

CONFIGPATH = './serverconf.ini'

# FixMe add module docstring. In particular, need to document
# module-level constants and server_config defined at the bottom of
# the file.

class Config:

    def __init__(self, path=CONFIGPATH):
        self._ensure_config(path)
        self.config = self._read_config(path)
        # _flesh_out_config does double duty, helping to ensure a
        # config file is on disk in _ensure_config; there the return
        # value is used, here not.
        _ = self._flesh_out_config(self.config)


    def _ensure_config(self, path):
        """Creates a default config file on disk if needed

        If neither the CONFIGPATH nor the path argument point to an
        existing configuration file, create a default config file at
        CONFIGPATH for future runs.
        """
        if os.path.exists(CONFIGPATH) or os.path.exists(path):
            return

        config = self._flesh_out_config()
        with open(CONFIGPATH, 'w') as configfile:
            config.write(configfile)


    def _flesh_out_config(self, config=None):
        """Returns a config object expanded to have default values

        The config argument is optional.

        If a configparser.ConfigParser instance is passed as the
        config argument, it will be extended as needed to ensure that
        there are values in its 'SERVER' section for 'host',
        'port' and 'logfilepath'.

        It nothing is passed as the config argument, a
        configparser.ConfigParser object will be created with default
        values in the 'SERVER' section as specified above.

        If any other value that evaluates to True is passed as the
        config argument, a ValueError Exception is raised.
        """
        if not config:
            config = configparser.ConfigParser()

        if not isinstance(config, configparser.ConfigParser):
            # Possibly over-kill as this method is not intended to be
            # called by clients.  Other methods of this class call
            # it only without argument or with a
            # configparser.ConfigParser object as argument. But, it is
            # worth having as a defence againstg the day when the
            # prior sentence ceases to be true.
            msg = ' '.join(
                'config must be a configparser.ConfigParser instance',
                'or evaluate to False')
            raise ValueError(msg)

        if not config.has_section('SERVER'):
            config['SERVER'] = {}

        for key, default_value in (
                ('host', HOST),
                ('port', str(PORT)), # Everything a string in config files
                ('logfilepath', LOGFILEPATH)):
            if not config.has_option('SERVER', key):
                config['SERVER'][key] = default_value

        return config


    def _read_config(self, path):
        """Returns a configparser.ConfigParser object

        Attempts to read the path into the ConfigParser object. If
        that causes a configparser.Error to be raised, it then tries
        to read CONFIGPATH into the ConfigParser object.
        """
        config = configparser.ConfigParser()
        try:
            config.read(path)
        except configparser.Error:
            # Then, something went awry. If we had a distinct path
            # argument, try reading the default and see if we cannot
            # carry forward:
            print("Couldn't read config from %s" %(path))
            if path != CONFIGPATH:
                # FixMe Really should log that the requested path was
                # ignored because somehow defective and CONFIGPATH
                # used instead.
                config = configparser.ConfigParser()
                config.read(CONFIGPATH)
                # FixMe Here and pasim, proper logging over stdout dumps
                print("Reading config from %s" %(CONFIGPATH))
            else:
                # Then, we really cannot recover:
                raise

        # Allow environment variables to over-ride config file values
        for key, envar in (
                ('host', 'HOST'),
                ('port', 'PORT'),
                ('logfilepath', 'LOGFILEPATH')):
            env_val = os.getenv(envar)
            if env_val:
                # FixMe proper logging instead of stdout
                print("Over-riding config value for %s with value %s of envar %s" %(
                    key, env_val, envar))
                config['SERVER'][key] = env_val

        if config['SERVER']['host'] == HOST:
            # HOST is the human friendly 'localhost'; replace with ip address
            config['SERVER']['host'] = '127.0.0.1'

        try:
            # Needed as if port set from envar, it will be a string.
            # (Also could arise from a user edit of the on disk config
            # file)
            int(config['SERVER']['port'])
        except ValueError:
            msg = ' '.join([
                "Got %s for the port;" %(config['SERVER']['port'],),
                "value must be an integer or convertible into one"])
            print(msg)
            sys.exit(1)

        return config


server_config = Config(CONFIGPATH).config['SERVER']
