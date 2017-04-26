import json
import os
import unittest
from unittest.mock import patch

from .context import jobnotify
from jobnotify.utils import EmailMatch


class MainTestCase(unittest.TestCase):
    """Test case for normal operation via `main`."""
    @classmethod
    def setUpClass(cls):
        cls.raw_response_path = os.path.join(jobnotify.TEST_DB_DIR, '.rawresponseshort.json')
        cls.cfg_filename = 'jobnotify.config.sample'
        cls.expected_db_filename = os.path.join(jobnotify.TEST_DB_DIR, 'scientist_dublin.json')

        with open(cls.raw_response_path, 'r') as f:
            cls.rawdb = json.load(f)

        # string version of database
        cls.dbs = json.dumps(cls.rawdb)

        cls.listings = (
            '1. Data Scientist @ Cpl Recruitment\n'
            'Link: http://ie.indeed.com/viewjob?jk=90feaf6e79c08d5f\n'
            'Location: Dublin\n'
            'Snippet: They have a unique opportunity for a talented and creative '
            'Data Scientist to join a world class team. My client are a cutting '
            'edge Analytics consultancy based...\n'
            '\n'
            '2. Internship - Bell Labs IP Platforms @ Nokia\n'
            'Link: http://ie.indeed.com/viewjob?jk=aa39943da620729a\n'
            'Location: Dublin\n'
            'Snippet: Serving customers in over 100 countries, our research '
            'scientists and engineers continue to invent and accelerate new '
            'technologies that will increasingly...\n'
        )

    @patch('smtplib.SMTP')
    @patch('urllib.request.urlopen')
    def test_jobnotify_good(self, mock_urlopen, mock_smtp):
        location = 'dublin'
        query = 'scientist'
        message = (
            f'Hello Matthew,\n\n'
            f'There are 2 new job listings to review.\n'
            f'The following job listings were found for {repr(query)} in '
            f'{repr(location)}:\n\n'
            f'{self.listings}\n'
            f'- T'
        )
        expected = {
            'subject': 'Job opportunities: 2 new jobs posted',
            'from': 'Job-Notify <test.sender@gmail.com>',
            'to': 'test.recipient@gmail.com',
            'message': message,
        }
        urlopen_instance = mock_urlopen.return_value.__enter__.return_value
        urlopen_instance.read.return_value = self.dbs.encode('utf-8')

        jobnotify.jobnotify(self.cfg_filename, jobnotify.TEST_DB_DIR)

        smtp_instance = mock_smtp.return_value.__enter__.return_value
        smtp_instance.send_message.assert_called_with(EmailMatch(expected))

    @patch('jobnotify.notify')
    @patch('urllib.request.urlopen')
    def test_jobnotify_keys_exist(self, mock_urlopen, mock_notify):
        urlopen_instance = mock_urlopen.return_value.__enter__.return_value
        urlopen_instance.read.return_value = self.dbs.encode('utf-8')

        d = {'90feaf6e79c08d5f': None, 'aa39943da620729a': None}

        # create a fake database with expected key entries
        with open(self.expected_db_filename, 'w') as f:
            json.dump(d, f)

        jobnotify.jobnotify(self.cfg_filename, jobnotify.TEST_DB_DIR)
        self.assertFalse(mock_notify.called)

    def tearDown(self):
        if os.path.isfile(self.expected_db_filename):
            os.remove(self.expected_db_filename)


if __name__ == '__main__':
    unittest.main()
