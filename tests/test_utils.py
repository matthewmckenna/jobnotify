from configparser import ConfigParser
# from itertools import dropwhile
# import io
import json
import os
# import shutil
# from tempfile import TemporaryFile
import unittest

from .context import jobnotify
from jobnotify.utils import (
    get_sanitised_params,
    get_section_configs,
    load_cfg,
    load_json_db,
    write_json_db,
)
from jobnotify.exceptions import (
    BlankKeyError,
    # ConfigurationFileError,
    NotificationsNotConfiguredError,
    RequiredKeyMissingError,
    SectionNotFoundError,
)


class ConfigFileTestCase(unittest.TestCase):
    """Test case for loading a configuration file."""
    @classmethod
    def setUpClass(cls):
        cls.indeed_reqs = {'key', 'query', 'location', 'country'}
        cls.email_reqs = {'email_to', 'email_from', 'password'}
        cls.slack_reqs = {'token', 'channel'}
        cls.notify_via_reqs = {'email', 'slack'}
        cls.sample_filename = 'cfg.ini.sample'
        cls.blank_key_filename = os.path.join('databases', '.blankkey')
        cls.no_notifications = os.path.join('databases', '.nonotifications')

        with open(cls.sample_filename) as f, open(cls.blank_key_filename, 'w') as g:
            _ = f.read().split('\n')
            # replace line which previously contained a sample key
            _[1] = 'key ='
            # reassemble the string before writing to file
            g.write('\n'.join(_))

        c = ConfigParser()
        c.read(cls.sample_filename)
        cls.expected_indeed_cfg = c['indeed']
        cls.expected_email_cfg = c['email']

        nv = c['notify_via']
        nv['email'] = 'false'
        with open(cls.no_notifications, 'w') as f:
            c.write(f)

    def test_no_config_file(self):
        """Test that we handle a config file not existing."""
        with self.assertRaises(FileNotFoundError):
            jobnotify.jobnotify(cfg_filename='fakefile.cfg')

    def test_invalid_section(self):
        """Test that we correctly handle an invalid section."""
        with self.assertRaises(SectionNotFoundError):
            load_cfg(self.sample_filename, section='fakesection', required=None)

    def test_good_indeed_key(self):
        """Test that we correctly return the Indeed API key."""
        cfg = load_cfg(self.sample_filename, section='indeed', required=self.indeed_reqs)
        self.assertEqual('4815162342', cfg['key'])

    def test_missing_requirement(self):
        """Test that we raise an error for missing key in config"""
        r = self.indeed_reqs.copy()
        # add speed and power to the requirements
        r.update({'speed', 'power'})
        with self.assertRaises(RequiredKeyMissingError):
            load_cfg(self.sample_filename, section='indeed', required=r)

    def test_blank_fields(self):
        """Test that we handle blank fields correctly."""
        with self.assertRaises(BlankKeyError):
            load_cfg(self.blank_key_filename, section='indeed', required=self.indeed_reqs)

    def test_load_multiple_configs_indeed(self):
        """Test that we load multiple configuration files correctly."""
        indeed_cfg, *_ = get_section_configs(self.sample_filename)
        self.assertEqual(self.expected_indeed_cfg, indeed_cfg)

    def test_load_multiple_configs_email(self):
        """Test that we load multiple configuration files correctly."""
        _, email_cfg, *_ = get_section_configs(self.sample_filename)
        self.assertEqual(self.expected_email_cfg, email_cfg)

    def test_load_multiple_configs_bad_config(self):
        """Test that we raise an exception for a config file error."""
        with self.assertRaises(BlankKeyError):
            get_section_configs(self.blank_key_filename)

    def test_notifications_not_configured(self):
        """Test we raise when notifications aren't configured."""
        with self.assertRaises(NotificationsNotConfiguredError):
            get_section_configs(self.no_notifications)

    @classmethod
    def tearDownClass(cls):
        os.remove(cls.blank_key_filename)


class DatabaseTestCase(unittest.TestCase):
    """Test case for handling the database."""
    @classmethod
    def setUpClass(cls):
        # TODO: Don't use databases dir
        cls.sample_database_name = os.path.join('databases', '.sampledb.json')
        cls.sample_write_db = os.path.join('databases', '.testdatabasewrite.json')
        cls.json_db = {
            "4da3f3ec1f781a3f":
                {
                    "company": "Brightwater Group",
                    "date_created": "Wed, 12 Apr 2017 13:21:11 GMT",
                    "desc": "Our client, a major, international banking brand, "
                    "currently has a job opening for a lead data scientist. "
                    "As a lead data Scientist sitting within the banks...",
                    "jobtitle": "Lead Data Scientist",
                    "lat": 53.332417,
                    "location": "Dublin",
                    "lon": -6.247253,
                    "url": "http://ie.indeed.com/viewjob?jk=4da3f3ec1f781a3f",
                }
        }
        # shutil.copy(cls.sample_database, os.path.join('databases'))
        with open(cls.sample_database_name, 'r') as f:
            cls.sample_db = json.load(f)
        # shutil.copy(source, dest)

    def test_load_existing_database(self):
        """Test that we correctly load a database if it exists."""
        db = load_json_db(self.sample_database_name)
        self.assertEqual(self.sample_db, db)

    def test_load_new_database(self):
        """Test that we create a new database if the filename is not found."""
        db = load_json_db('.madeupdatabasethatshouldnotexist.json')
        self.assertEqual(db, {})

    def test_sanitise_query(self):
        """Test that we correctly sanitise a database name."""
        query, location = get_sanitised_params(q='electronic engineer', l='dublin')
        expected_sanitised_query = 'electronic_engineer'
        self.assertEqual(expected_sanitised_query, query)

    def test_sanitise_location(self):
        """Test that we correctly sanitise a location."""
        query, location = get_sanitised_params(q='data scientist', l='new york city')
        expected_sanitised_location = 'new_york_city'
        self.assertEqual(expected_sanitised_location, location)

    def test_database_write(self):
        """Test that we write a file to disk without issue."""
        write_json_db(self.json_db, self.sample_write_db)
        self.assertTrue(os.path.isfile(self.sample_write_db))

    @classmethod
    def tearDownClass(cls):
        os.remove(cls.sample_write_db)


if __name__ == '__main__':
    unittest.main()
