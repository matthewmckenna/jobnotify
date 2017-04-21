from configparser import ConfigParser
import email
import json
import os
# import shutil
import unittest
from unittest.mock import patch
# from urllib.parse import urlencode
# from urllib.request import urlopen

# from .context import jobnotify
from jobnotify import INDEED_BASE_URL, build_url, construct_email, send_email


class BuildURLTestCase(unittest.TestCase):
    """Test case for contstructing valid URLs."""
    @classmethod
    def setUpClass(cls):
        cls.simple_params = {
            'publisher': 4815162342,
            'q': 'data scientist',
            'l': 'dublin',
            'radius': 10,
            'jt': 'fulltime',
            'limit': 25,
            'fromage': 10,
            'start': 0,
            'highlight': 0,
            'latlong': 1,
            'co': 'ie',
            'v': 2,
            'format': 'json',
        }

    def test_build_url(self):
        """Test that we construct a good URL."""
        expected_encode_result = (
            'publisher=4815162342&q=data+scientist&l=dublin&radius=10&jt=fulltime&'
            'limit=25&fromage=10&start=0&highlight=0&latlong=1&co=ie&v=2&format=json'
        )
        expected_url = f'{INDEED_BASE_URL}?{expected_encode_result}'
        url = build_url(INDEED_BASE_URL, self.simple_params)
        self.assertEqual(expected_url, url)


class EmailTestCase(unittest.TestCase):
    """Test case for constructing emails."""
    @classmethod
    def setUpClass(cls):
        cls.query = 'scientist'
        cls.location = 'dublin'
        cls.signature = '- T'
        cls.sample_cfg_filename = 'cfg.ini.sample'
        cls.sample_database_name = os.path.join('databases', '.sampledb.json')
        cls.no_opt_params_filename = 'cfg.no_opt_params'

        with open(cls.sample_database_name, 'r') as f:
            db = json.load(f)
            cls.db = db.copy()
            # delete key e90a42701d1d29ec leave key 4da3f3ec1f781a3f from local db
            del db['e90a42701d1d29ec']
            cls.single_job_db = db.copy()

        with open(cls.sample_cfg_filename) as f, open(cls.no_opt_params_filename, 'w') as g:
            cfg = f.read().split('\n')
            # find the start and end line numbers for optional parameters
            start, end = [i for i, line in enumerate(cfg) if line[:4] == '####']
            # write to file without the last seven lines of the file
            g.write('\n'.join(cfg[:start]+cfg[end+2:]))

        c = ConfigParser()
        c.read(cls.sample_cfg_filename)
        cls.cfg = c['email']

        c2 = ConfigParser()
        c2.read(cls.no_opt_params_filename)
        cls.cfg_no_opt = c2['email']

    def test_email_construction_single_job(self):
        """Test we construct an email for a single job correctly."""
        listing = (
            '1. Lead Data Scientist @ Brightwater Group\n'
            'Link: http://ie.indeed.com/viewjob?jk=4da3f3ec1f781a3f\n'
            'Location: Dublin\n'
            'Snippet: Our client, a major, international banking brand, currently '
            'has a job opening for a lead data scientist. As a lead data Scientist '
            'sitting within the banks...\n'
        )
        expected_string = (
            f'From: Job-Notify <test.sender@gmail.com>\n'
            f'To: test.recipient@gmail.com\n'
            f'Subject: Job opportunities: 1 new job posted\n'
            f'Hello Matthew,\n\n'
            f'There is 1 new job listing to review.\n'
            f'The following job listing was found for {repr(self.query)} in '
            f'{repr(self.location)}:\n\n'
            f'{listing}\n'
            f'{self.signature}'
        )

        s = construct_email(self.cfg, self.query, self.location, self.single_job_db)
        self.assertEqual(expected_string, s)

    def test_email_construction_multiple_jobs(self):
        """Test we construct an email with > 1 job correctly."""

        listings = (
            '1. Lead Data Scientist @ Brightwater Group\n'
            'Link: http://ie.indeed.com/viewjob?jk=4da3f3ec1f781a3f\n'
            'Location: Dublin\n'
            'Snippet: Our client, a major, international banking brand, currently '
            'has a job opening for a lead data scientist. As a lead data Scientist '
            'sitting within the banks...\n'
            '\n'
            '2. Research Fellow (Data Science/Biomedical Engineering) @ Trinity College Dublin\n'
            'Link: http://ie.indeed.com/viewjob?jk=e90a42701d1d29ec\n'
            'Location: Dublin\n'
            'Snippet: The investigator will join a vibrant inter-disciplinary '
            'team - including epidemiologists, biostatisticians, economists, '
            'social scientists, biomedical engineers...\n'
        )

        expected_string = (
            f'From: Job-Notify <test.sender@gmail.com>\n'
            f'To: test.recipient@gmail.com\n'
            f'Subject: Job opportunities: 2 new jobs posted\n'
            f'Hello Matthew,\n\n'
            f'There are 2 new job listings to review.\n'
            f'The following job listings were found for {repr(self.query)} in '
            f'{repr(self.location)}:\n\n'
            f'{listings}\n'
            f'{self.signature}'
        )

        s = construct_email(self.cfg, self.query, self.location, self.db)
        self.assertEqual(expected_string, s)

    def test_email_construction_without_optional_params(self):
        """Test we construct a valid email when optional params are missing."""
        listing = (
            '1. Lead Data Scientist @ Brightwater Group\n'
            'Link: http://ie.indeed.com/viewjob?jk=4da3f3ec1f781a3f\n'
            'Location: Dublin\n'
            'Snippet: Our client, a major, international banking brand, currently '
            'has a job opening for a lead data scientist. As a lead data Scientist '
            'sitting within the banks...\n'
        )
        expected_string = (
            f'From: test.sender@gmail.com <test.sender@gmail.com>\n'
            f'To: test.recipient@gmail.com\n'
            f'Subject: Job opportunities: 1 new job posted\n'
            f'Hello test.recipient,\n\n'
            f'There is 1 new job listing to review.\n'
            f'The following job listing was found for {repr(self.query)} in '
            f'{repr(self.location)}:\n\n'
            f'{listing}\n'
            # f'{self.signature}'
        )

        s = construct_email(self.cfg_no_opt, self.query, self.location, self.single_job_db)
        self.assertEqual(expected_string, s)

    @classmethod
    def tearDownClass(cls):
        os.remove(cls.no_opt_params_filename)


class NotifyTestCase(unittest.TestCase):
    """Test case for sending notifications."""
    @classmethod
    def setUpClass(cls):
        cls.query = 'scientist'
        cls.location = 'dublin'
        # cls.reqs = {'email_to', 'email_from', 'password'}
        # cls.email_cfg = load_cfg('cfg.ini.sample', 'email', cls.reqs)
        cls.email_cfg = {'email_from': 'test@gmail.com', 'password': 'test1234'}
        # def notify(email_cfg, posts, query, location):

    @patch('smtplib.SMTP')
    def test_notify(self, mock_smtp):
        # with patch('smtplib.SMTP') as mock_smtp:
        listings = (
            '1. Lead Data Scientist @ Brightwater Group\n'
            'Link: http://ie.indeed.com/viewjob?jk=4da3f3ec1f781a3f\n'
            'Location: Dublin\n'
            'Snippet: Our client, a major, international banking brand, currently '
            'has a job opening for a lead data scientist. As a lead data Scientist '
            'sitting within the banks...\n'
            '\n'
            '2. Research Fellow (Data Science/Biomedical Engineering) @ Trinity College Dublin\n'
            'Link: http://ie.indeed.com/viewjob?jk=e90a42701d1d29ec\n'
            'Location: Dublin\n'
            'Snippet: The investigator will join a vibrant inter-disciplinary '
            'team - including epidemiologists, biostatisticians, economists, '
            'social scientists, biomedical engineers...\n'
        )

        message = (
            f'From: Job-Notify <test.sender@gmail.com>\n'
            f'To: test.recipient@gmail.com\n'
            f'Subject: Job opportunities: 2 new jobs posted\n'
            f'Hello Matthew,\n\n'
            f'There are 2 new job listings to review.\n'
            f'The following job listings were found for {repr(self.query)} in '
            f'{repr(self.location)}:\n\n'
            f'{listings}\n'
            f'- T'
        )

        msg = email.message_from_string(message)
        msg.set_charset('utf-8')

        send_email(self.email_cfg['email_from'], self.email_cfg['password'], msg)
        instance = mock_smtp.return_value.__enter__.return_value
        # self.assertEqual(mock_smtp.call_count, 2)
        instance.send_message.assert_called_once_with(msg)
        # self.assertTrue(instance.ehlo.called)


if __name__ == '__main__':
    unittest.main()
