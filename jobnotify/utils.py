# from collections import defaultdict
import argparse
import base64
import configparser
import json
import os
from pkg_resources import resource_filename
import shutil
# import sys

from .exceptions import (
    BlankKeyError,
    # ConfigurationFileError,
    NotificationsNotConfiguredError,
    RequiredKeyMissingError,
    SectionNotFoundError,
)


class EmailMatch:
    """Helper class to compare properties of emails."""
    def __init__(self, expected):
        self.expected = expected

    def __eq__(self, other):
        return (
            self.expected['from'] == other['from'] and
            self.expected['to'] == other['to'] and
            self.expected['subject'] == other['subject'] and
            self.expected['message'] == base64.b64decode(other.get_payload()).decode('utf-8')
        )

    def __ne__(self, other):
        """Define a non-equality test"""
        return not self.__eq__(other)

    def __repr__(self):
        return (
            f'From: {self.expected["from"]}\n'
            f'To: {self.expected["to"]}\n'
            f'Subject: {self.expected["subject"]}\n'
            f'Message: {self.expected["message"]}'
        )


def get_sanitised_params(q, l):
    """Remove spaces from params and make lowercase."""
    # TODO: Tidy this string replacement
    query = q.lower().replace(' ', '_').replace('-', '_')
    loc = l.lower().replace(' ', '_').replace('-', '_')

    return query, loc


def load_json_db(path_to_db):
    """Load and return a JSON database.

    Return a JSON database if it exists, otherwise return
    an empty dict.

    Args:
        path_to_db: path to the database.

    Returns:
        db: JSON database, or empty dict

    """
    if not os.path.isfile(path_to_db):
        db = {}
    else:
        with open(path_to_db, 'r') as f:
            db = json.load(f)

    return db


def load_cfg(fname, section, required):
    """Load `section` from configuration file.

    Args:
        section: the section from the configuration file to return
        required: a list of required keys for this section

    Returns:
        dict-like section from configuration file.

    Raises:
        ConfigurationFileError: if `section` missing from file, or
            if required keys are missing.
        configparser.DuplicateOptionError: if there is a duplicate
            key in any section.
    """
    cfg = configparser.ConfigParser()
    cfg.read(fname)

    try:
        cfg_section = cfg[section]
    except KeyError:
        raise SectionNotFoundError(
            f'Section {repr(section)} not found in configuration file.'
        )

    # if the section is missing any of the required keys
    # set-based operation
    if not cfg_section.keys() >= required:
        missing_keys = required - cfg_section.keys()
        raise RequiredKeyMissingError(
            f'Key(s) {missing_keys} keys missing from configuration file.'
        )

    # check that there are no blank fields in the config file
    blank_keys = []
    for k, v in cfg_section.items():
        if not v:
            blank_keys.append(k)

    # TODO: Handle grammar a little better by checking len(blank_keys)
    if blank_keys:
        raise BlankKeyError(f'Key(s) {blank_keys} in {repr(section)} section are blank.')

    return cfg_section


def get_section_configs(filename):
    """Returns sections from configuration file.

    Args:
        filename: configuration filename

    Raises:
        NotificationsNotConfiguredError: if all options in
            `notify_via` section of configuration file are
            set to `false`.

    Returns:
        list of configuration sections.
    """
    # TODO: Can this be turned into a generator?
    cfgs = []

    # TODO: pass in this structure
    section_reqs = [
        ('indeed', {'key', 'query', 'location', 'country'}),
        ('email', {'email_from', 'email_to', 'password'}),
        ('slack', {'token', 'channel'}),
        ('notify_via', {'email', 'slack'}),
    ]

    # TODO: Perhaps handle errors at higher level?
    for section, requirements in section_reqs:
        cfgs.append(load_cfg(filename, section, requirements))

    # `notify_via` is the last cfg section added above
    nv = cfgs[-1]

    if not any(nv.getboolean(k) for k in nv.keys()):
        raise NotificationsNotConfiguredError(
            'Notifications must be set for at least one option.'
        )
        # try:
        #     cfgs.append(load_cfg(filename, section, requirements))
        # except (ConfigurationFileError, DuplicateOptionError) as e:
        #     print(f'ERROR: {e}')
        #     logging.exception(e)
        #     sys.exit()

    return cfgs


def write_json_db(db, path_to_db):
    """Write `db` to file."""
    with open(path_to_db, 'w') as f:
        # with open(os.path.join(DB_DIR, db_name), 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, sort_keys=True)


def initial_setup(app_data_dir):
    """Create files needed for `jobnotify` application."""
    config_fn = resource_filename(__name__, 'jobnotify.config.sample')
    # print(config_fn)

    # application directory does not exist - create it
    if not os.path.isdir(app_data_dir):
        os.mkdir(app_data_dir)
        os.mkdir(os.path.join(app_data_dir, 'databases'))
        shutil.copy(config_fn, os.path.join(app_data_dir, 'jobnotify.config'))
    else:
        if not os.path.isdir(os.path.join(app_data_dir, 'databases')):
            os.mkdir(os.path.join(app_data_dir, 'databases'))

        # check that the configuration file exists
        if not os.path.exists(os.path.join(app_data_dir, 'jobnotify.config')):
            # shutil.copy(src, dst)
            shutil.copy(config_fn, os.path.join(app_data_dir, 'jobnotify.config'))


def process_args(
    args=None,
    *,
    path_to_cfg=os.path.join(os.path.expanduser('~'), '.jobnotify', 'jobnotify.config')
):
    """Parse and process command line arguments.

    Args:
        args: command line arguments
        path_to_cfg: path to the default configuration file.

    Returns:
        args: argparse.Namespace object with attributes of
            command line arguments.
    """
    if args is None:
        args = []

    parser = argparse.ArgumentParser(
        description='Send notifications about new job listings.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '-v',
        '--verbose',
        help='enable logging to file',
        action='store_true'
    )
    parser.add_argument(
        '-c',
        '--config',
        help='path to configuration file',
        default=path_to_cfg
    )
    return parser.parse_args(args)
