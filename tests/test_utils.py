from configparser import ConfigParser
# from itertools import dropwhile
# import io
import email
import json
import os
# import shutil
from tempfile import TemporaryDirectory
import unittest

from .context import jobnotify, SAMPLE_CFG_FILE_PATH, TEST_DB_DIR
from jobnotify.utils import (
    EmailMatch,
    get_sanitised_params,
    get_section_configs,
    initial_setup,
    load_cfg,
    load_json_db,
    process_args,
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
        cls.sample_filename = SAMPLE_CFG_FILE_PATH
        cls.blank_key_filename = os.path.join(TEST_DB_DIR, '.blankkey')
        cls.no_notifications = os.path.join(TEST_DB_DIR, '.nonotifications')

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
        os.remove(cls.no_notifications)


class DatabaseTestCase(unittest.TestCase):
    """Test case for handling the database."""
    @classmethod
    def setUpClass(cls):
        cls.sample_database_name = os.path.join(TEST_DB_DIR, '.sampledb.json')
        cls.sample_write_db = os.path.join(TEST_DB_DIR, '.testdatabasewrite.json')
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


class EmailMatchTestCase(unittest.TestCase):
    """Test case for the EmailMatch helper class"""
    def test_message_does_not_match(self):
        location = 'dublin'
        query = 'scientist'
        listings = (
            '1. Lead Data Scientist @ Brightwater Group\n'
            'Link: http://ie.indeed.com/viewjob?jk=4da3f3ec1f781a3f\n'
            'Location: Dublin\n'
            'Snippet: Our client, a major, international banking brand, currently '
            'has a job opening for a lead data scientist. As a lead data Scientist '
            'sitting within the banks...\n'
        )

        body = (
            f'Hello test.recipient,\n\n'
            f'There are 2 new job listings to review.\n'
            f'The following job listings were found for {repr(query)} in '
            f'{repr(location)}:\n\n'
            f'{listings}\n'
            f'- T'
        )

        message = (
            f'From: test.sender@gmail.com <test.sender@gmail.com>\n'
            f'To: test.recipient@gmail.com\n'
            f'Subject: Job opportunities: 2 new jobs posted\n'
            f'{body}'
        )

        # bad subject line in expected message
        expected = {
            'subject': 'Incorrect subject line',
            'from': 'test.sender@gmail.com <test.sender@gmail.com>',
            'to': 'test.recipient@gmail.com',
            'message': body,
        }

        msg = email.message_from_string(message)
        msg.set_charset('utf-8')

        self.assertNotEqual(EmailMatch(expected), msg)


class InitialSetupTestCase(unittest.TestCase):
    """Test case for creating required directories and files."""
    @classmethod
    def setUpClass(cls):
        cls.app_data_dir_name = '.jobconfig'
        cls.config_filename = 'jobnotify.config'
        cls.sample_cfg_filename = SAMPLE_CFG_FILE_PATH
        with open(cls.sample_cfg_filename, 'r') as f:
            cls.sample_cfg = f.read()

    def test_app_data_dir_does_not_exist_create_app_data_dir(self):
        """Test we create all necessary directories and files from scratch."""
        with TemporaryDirectory() as dirname:
            app_data_dir = os.path.join(dirname, self.app_data_dir_name)
            initial_setup(app_data_dir)
            self.assertTrue(os.path.isdir(app_data_dir))

    def test_app_data_dir_does_not_exist_create_databases_dir(self):
        """Test we create all necessary directories and files from scratch."""
        with TemporaryDirectory() as dirname:
            app_data_dir = os.path.join(dirname, self.app_data_dir_name)
            db_dir = os.path.join(app_data_dir, 'databases')
            initial_setup(app_data_dir)
            self.assertTrue(os.path.isdir(db_dir))

    def test_app_data_dir_does_not_exist_create_config_file(self):
        """Test we create all necessary directories and files from scratch."""
        with TemporaryDirectory() as dirname:
            app_data_dir = os.path.join(dirname, self.app_data_dir_name)
            initial_setup(app_data_dir)
            # path to the created configuration file
            cfg_path = os.path.join(app_data_dir, self.config_filename)
            with open(cfg_path, 'r') as f:
                cfg = f.read()

            self.assertEqual(self.sample_cfg, cfg)

    def test_app_data_dir_exists_create_databases_dir(self):
        """Test we create all necessary directories and files from scratch."""
        with TemporaryDirectory() as dirname:
            app_data_dir = os.path.join(dirname, self.app_data_dir_name)
            os.mkdir(app_data_dir)
            db_dir = os.path.join(app_data_dir, 'databases')
            initial_setup(app_data_dir)
            self.assertTrue(os.path.isdir(db_dir))

    def test_app_data_dir_exists_create_cfg_file(self):
        """Test we create all necessary directories and files from scratch."""
        with TemporaryDirectory() as dirname:
            app_data_dir = os.path.join(dirname, self.app_data_dir_name)
            initial_setup(app_data_dir)

            # path to the created configuration file
            cfg_path = os.path.join(app_data_dir, self.config_filename)

            with open(cfg_path, 'r') as f:
                cfg = f.read()

            self.assertEqual(self.sample_cfg, cfg)


class ProcessArgsTestCase(unittest.TestCase):
    """Test case for argument parsing"""
    def test_process_verbose_flag(self):
        args = process_args(['-v'])
        self.assertTrue(args.verbose)

    def test_process_path_to_config_file(self):
        path_to_config = 'made/up/path/to/jobnotify.config'
        args = process_args(['--config', path_to_config])
        self.assertEqual(args.config, path_to_config)

    def test_process_args_no_args_passed_good_cfg_path(self):
        path_to_config = os.path.join(
            os.path.expanduser('~'), '.jobnotify', 'jobnotify.config'
        )
        args = process_args()
        self.assertEqual(args.config, path_to_config)

    def test_process_args_no_args_passed_good_verbose_flag(self):
        args = process_args()
        self.assertFalse(args.verbose)


if __name__ == '__main__':
    unittest.main()
