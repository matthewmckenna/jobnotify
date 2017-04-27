from configparser import ConfigParser
import email
import json
import os
# import shutil
import unittest
from unittest.mock import call, patch
# from urllib.parse import urlencode
# from urllib.request import urlopen

from .context import SAMPLE_CFG_FILE_PATH, TEST_DB_DIR
from jobnotify import (
    build_url,
    construct_email,
    construct_slack_message,
    email_notify,
    indeed_api_request,
    INDEED_BASE_URL,
    notify,
    send_email,
    slack_notify,
)
from jobnotify.exceptions import (
    EmailAuthenticationError,
    IndeedAuthenticationError,
    SlackCfgError,
)
from jobnotify.utils import EmailMatch


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


class SlackTestCase(unittest.TestCase):
    """Test case for constructing and sending Slack messages."""
    @classmethod
    def setUpClass(cls):
        cls.sample_db_name = os.path.join(TEST_DB_DIR, '.sampledb.json')
        cls.sample_large_db_name = os.path.join(TEST_DB_DIR, '.samplelargedb.json')
        with open(cls.sample_db_name) as f, open(cls.sample_large_db_name) as g:
            cls.small_db = json.load(f)
            cls.large_db = json.load(g)

    def test_construct_short_message(self):
        """Test we correctly construct a short message."""
        expected_result = [
            '1. <http://ie.indeed.com/viewjob?jk=4da3f3ec1f781a3f|Lead Data '
            'Scientist @ Brightwater Group>\n'
            'Snippet: Our client, a major, international banking brand, currently '
            'has a job opening for a lead data scientist. As a lead data Scientist '
            'sitting within the banks...\n\n'
            '2. <http://ie.indeed.com/viewjob?jk=e90a42701d1d29ec|Research '
            'Fellow (Data Science/Biomedical Engineering) @ Trinity College Dublin>\n'
            'Snippet: The investigator will join a vibrant inter-disciplinary team '
            '- including epidemiologists, biostatisticians, economists, social '
            'scientists, biomedical engineers...\n'
        ]
        msg_it = construct_slack_message(self.small_db)
        self.assertEqual(expected_result, msg_it)

    def test_construct_long_message(self):
        """Test we construct a long message correctly."""
        expected_result = [
            '1. <http://ie.indeed.com/viewjob?jk=265d0ec5b7dcaa77|Lecturer / '
            'Assistant Professor of the Business of Biotechnology @ UCD School '
            'of Biomolecular and Biomedical Science (SBBS) - University College '
            'Dublin>\n'
            'Snippet: We are looking to recruit an individual with a proven track '
            'record of research and expertise in the areas of feasibility studies '
            'and business planning who will...\n\n'
            '2. <http://ie.indeed.com/viewjob?jk=3d0cbb963296f558|Team Lead in '
            'Process Development R&D @ APC Ltd>\n'
            'Snippet: Lead an interdisciplinary team of engineers, scientists and '
            'analysts on the development, optimisation, scale-up and tech transfer '
            'of small molecule processes....\n\n'
            '3. <http://ie.indeed.com/viewjob?jk=412fc7ec2764f736|PhD Studentship '
            '@ Trinity College Dublin, The University of Dublin>\n'
            'Snippet: Ireland\u2019s first purpose-built nanoscience research '
            'institute, CRANN, houses 150 scientists, technicians and graduate '
            'students in specialised laboratory...\n\n'
            '4. <http://ie.indeed.com/viewjob?jk=4da3f3ec1f781a3f|Lead Data '
            'Scientist @ Brightwater Group>\n'
            'Snippet: Our client, a major, international banking brand, currently '
            'has a job opening for a lead data scientist. As a lead data Scientist '
            'sitting within the banks...\n\n'
            '5. <http://ie.indeed.com/viewjob?jk=516d904d367e6255|Research '
            'Fellow (Data Science/Biomedical Engineering) @ Trinity College>\n'
            'Snippet: The investigator will join a vibrant inter-disciplinary team '
            '- including epidemiologists, biostatisticians, economists, social '
            'scientists, biomedical engineers...\n\n'
            '6. <http://ie.indeed.com/viewjob?jk=59535ea1597dce8d|Strength & '
            'Conditioning Coach/Sport Scientist @ Sports Surgery Clinic>\n'
            'Snippet: The Department is seeking an additional Strength and '
            'Conditioning Coach/Sports Scientist to provide technical support '
            'and expertise nationally and...\n\n'
            '7. <http://ie.indeed.com/viewjob?jk=61430a6d73819a90|Team Lead in '
            'Bioprocess Development R&D @ APC Ltd>\n'
            'Snippet: Lead an interdisciplinary team of engineers, scientists and '
            'analysts on the development, optimisation, scale-up and tech transfer '
            'of large molecule processes....\n\n'
            '8. <http://ie.indeed.com/viewjob?jk=b8bd1da87b9489d6|Lecturer/Assistant '
            'Professor of the Business of Biotechnology @ University College Dublin>\n'
            'Snippet: We are looking to recruit an individual with a proven track '
            'record of research and expertise in the areas of feasibility studies '
            'and business planning who will...\n\n'
            '9. <http://ie.indeed.com/viewjob?jk=b96b0df8da3448f4|Pharmacovigilance '
            'Scientist Contract @ Thornshaw Recruitment>\n'
            'Snippet: Our client , a global pharmaceutical company, are currently '
            'recruiting for a Pharmacovigilance Scientist role....\n\n'
            '10. <http://ie.indeed.com/viewjob?jk=c0892a9d74fb1c75|Head of Function '
            '@ Cpl Recruitment>\n'
            'Snippet: Our team of engineers and scientists are building software '
            'that sifts through billions of event data to make millions of decisions '
            'every day....\n\n',
            '11. <http://ie.indeed.com/viewjob?jk=d0244e76a6c873a7|Post-Doc Cloud '
            'Research Scientist @ Nokia>\n'
            'Snippet: Serving customers in over 100 countries, our research '
            'scientists and engineers continue to invent and accelerate new '
            'technologies that will increasingly...\n\n'
            '12. <http://ie.indeed.com/viewjob?jk=e90a42701d1d29ec|Research Fellow '
            '(Data Science/Biomedical Engineering) @ Trinity College Dublin>\n'
            'Snippet: The investigator will join a vibrant inter-disciplinary team '
            '- including epidemiologists, biostatisticians, economists, social '
            'scientists, biomedical engineers...\n'
        ]
        msg_it = construct_slack_message(self.large_db)
        self.assertEqual(expected_result, list(msg_it))

    @patch('slackclient.SlackClient.api_call')
    def test_notify_short_message(self, mock_sc):
        """Test for notification via Slack for short message."""
        cfg = {'token': 'xoxb-0123456789', 'channel': '#jobs'}
        slack_notify(cfg, self.small_db)
        msg = (
            '1. <http://ie.indeed.com/viewjob?jk=4da3f3ec1f781a3f|Lead Data '
            'Scientist @ Brightwater Group>\n'
            'Snippet: Our client, a major, international banking brand, currently '
            'has a job opening for a lead data scientist. As a lead data Scientist '
            'sitting within the banks...\n\n'
            '2. <http://ie.indeed.com/viewjob?jk=e90a42701d1d29ec|Research '
            'Fellow (Data Science/Biomedical Engineering) @ Trinity College Dublin>\n'
            'Snippet: The investigator will join a vibrant inter-disciplinary team '
            '- including epidemiologists, biostatisticians, economists, social '
            'scientists, biomedical engineers...\n'
        )
        calls = [
            call('api.test'),
            call(
                'chat.postMessage',
                text=msg,
                channel=cfg['channel'],
                icon_emoji=':robot_face:',
            ),
        ]
        # pass `any_order=True` as there are two implicit calls to __getitem__
        # made when checking the `ok` field of the response
        mock_sc.assert_has_calls(calls, any_order=True)

    @patch('slackclient.SlackClient.api_call')
    def test_bad_ok(self, mock_sc):
        """Test that we raise for a bad response."""
        cfg = {'token': 'xoxb-0123456789', 'channel': '#jobs'}
        mock_sc.return_value = {'ok': False, 'error': 'test_bad_response'}
        with self.assertRaises(SlackCfgError):
            slack_notify(cfg, self.small_db)


class EmailTestCase(unittest.TestCase):
    """Test case for constructing emails."""
    @classmethod
    def setUpClass(cls):
        cls.query = 'scientist'
        cls.location = 'dublin'
        cls.signature = '- T'
        cls.sample_cfg_filename = SAMPLE_CFG_FILE_PATH
        cls.sample_database_name = os.path.join(TEST_DB_DIR, '.sampledb.json')
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
        cls.email_cfg = {
            'email_from': 'test.sender@gmail.com',
            'password': 'test1234',
            'email_to': 'test.recipient@gmail.com',
        }
        cls.sample_db_name = os.path.join(TEST_DB_DIR, '.sampledb.json')
        cls.sample_cfg_path = SAMPLE_CFG_FILE_PATH

        c = ConfigParser()
        c.read(cls.sample_cfg_path)
        cls.cfgs_email_route = [c['indeed'], c['email'], c['slack'], c['notify_via']]

        # notify via Slack only
        c2 = ConfigParser()
        c2.read(cls.sample_cfg_path)
        nv = c2['notify_via']
        nv['email'] = 'false'
        nv['slack'] = 'true'
        cls.cfgs_slack_route = [c2['indeed'], c2['email'], c2['slack'], c2['notify_via']]

        # notify via email and Slack
        c3 = ConfigParser()
        c3.read(cls.sample_cfg_path)
        nv = c3['notify_via']
        nv['slack'] = 'true'
        cls.cfgs_all_routes = [c3['indeed'], c3['email'], c3['slack'], c3['notify_via']]

        cls.listings = (
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

        with open(cls.sample_db_name, 'r') as f:
            cls.posts = json.load(f)

    @patch('smtplib.SMTP')
    def test_send_email(self, mock_smtp):
        message = (
            f'From: Job-Notify <test.sender@gmail.com>\n'
            f'To: test.recipient@gmail.com\n'
            f'Subject: Job opportunities: 2 new jobs posted\n'
            f'Hello Matthew,\n\n'
            f'There are 2 new job listings to review.\n'
            f'The following job listings were found for {repr(self.query)} in '
            f'{repr(self.location)}:\n\n'
            f'{self.listings}\n'
            f'- T'
        )

        msg = email.message_from_string(message)
        msg.set_charset('utf-8')

        send_email(self.email_cfg['email_from'], self.email_cfg['password'], msg)
        instance = mock_smtp.return_value.__enter__.return_value
        instance.send_message.assert_called_once_with(msg)

    def test_send_email_bad_user_pass(self):
        """Test we raise an exception for bad authentication details."""
        message = (
            f'From: Job-Notify <test.sender@gmail.com>\n'
            f'To: test.recipient@gmail.com\n'
            f'Subject: Job opportunities: 2 new jobs posted\n'
            f'Hello Matthew,\n\n'
            f'There are 2 new job listings to review.\n'
            f'The following job listings were found for {repr(self.query)} in '
            f'{repr(self.location)}:\n\n'
            f'{self.listings}\n'
            f'- T'
        )

        msg = email.message_from_string(message)
        msg.set_charset('utf-8')
        with self.assertRaises(EmailAuthenticationError):
            email_notify(self.email_cfg, self.posts, self.query, self.location)

    @patch('smtplib.SMTP')
    def test_email_notify(self, mock_smtp):
        message = (
            f'Hello test.recipient,\n\n'
            f'There are 2 new job listings to review.\n'
            f'The following job listings were found for {repr(self.query)} in '
            f'{repr(self.location)}:\n\n'
            f'{self.listings}\n'
        )
        expected = {
            'subject': 'Job opportunities: 2 new jobs posted',
            'from': 'test.sender@gmail.com <test.sender@gmail.com>',
            'to': 'test.recipient@gmail.com',
            'message': message,
        }

        email_notify(self.email_cfg, self.posts, self.query, self.location)
        instance = mock_smtp.return_value.__enter__.return_value
        instance.send_message.assert_called_with(EmailMatch(expected))

    @patch('smtplib.SMTP')
    def test_general_notify_email_route(self, mock_smtp):
        message = (
            f'Hello Matthew,\n\n'
            f'There are 2 new job listings to review.\n'
            f'The following job listings were found for {repr(self.query)} in '
            f'{repr(self.location)}:\n\n'
            f'{self.listings}\n'
            f'- T'
        )
        expected = {
            'subject': 'Job opportunities: 2 new jobs posted',
            'from': 'Job-Notify <test.sender@gmail.com>',
            'to': 'test.recipient@gmail.com',
            'message': message,
        }

        notify(self.cfgs_email_route, self.posts)
        instance = mock_smtp.return_value.__enter__.return_value
        instance.send_message.assert_called_with(EmailMatch(expected))

    @patch('slackclient.SlackClient.api_call')
    def test_general_notify_slack_route(self, mock_sc):
        expected = (
            '1. <http://ie.indeed.com/viewjob?jk=4da3f3ec1f781a3f|Lead Data '
            'Scientist @ Brightwater Group>\n'
            'Snippet: Our client, a major, international banking brand, currently '
            'has a job opening for a lead data scientist. As a lead data Scientist '
            'sitting within the banks...\n\n'
            '2. <http://ie.indeed.com/viewjob?jk=e90a42701d1d29ec|Research '
            'Fellow (Data Science/Biomedical Engineering) @ Trinity College Dublin>\n'
            'Snippet: The investigator will join a vibrant inter-disciplinary team '
            '- including epidemiologists, biostatisticians, economists, social '
            'scientists, biomedical engineers...\n'
        )
        expected_channel = '#jobs'

        notify(self.cfgs_slack_route, self.posts)

        calls = [
            call('api.test'),
            call(
                'chat.postMessage',
                text=expected,
                channel=expected_channel,
                icon_emoji=':robot_face:',
            ),
        ]
        # pass `any_order=True` as there are two implicit calls to __getitem__
        # made when checking the `ok` field of the response
        mock_sc.assert_has_calls(calls, any_order=True)

    @patch('slackclient.SlackClient.api_call')
    @patch('smtplib.SMTP')
    def test_both_routes(self, mock_smtp, mock_sc):
        """Test that having both routes on works as expected."""
        message = (
            f'Hello Matthew,\n\n'
            f'There are 2 new job listings to review.\n'
            f'The following job listings were found for {repr(self.query)} in '
            f'{repr(self.location)}:\n\n'
            f'{self.listings}\n'
            f'- T'
        )
        expected_email = {
            'subject': 'Job opportunities: 2 new jobs posted',
            'from': 'Job-Notify <test.sender@gmail.com>',
            'to': 'test.recipient@gmail.com',
            'message': message,
        }
        expected_slack_msg = (
            '1. <http://ie.indeed.com/viewjob?jk=4da3f3ec1f781a3f|Lead Data '
            'Scientist @ Brightwater Group>\n'
            'Snippet: Our client, a major, international banking brand, currently '
            'has a job opening for a lead data scientist. As a lead data Scientist '
            'sitting within the banks...\n\n'
            '2. <http://ie.indeed.com/viewjob?jk=e90a42701d1d29ec|Research '
            'Fellow (Data Science/Biomedical Engineering) @ Trinity College Dublin>\n'
            'Snippet: The investigator will join a vibrant inter-disciplinary team '
            '- including epidemiologists, biostatisticians, economists, social '
            'scientists, biomedical engineers...\n'
        )
        expected_channel = '#jobs'

        notify(self.cfgs_all_routes, self.posts)

        instance = mock_smtp.return_value.__enter__.return_value
        instance.send_message.assert_called_with(EmailMatch(expected_email))

        calls = [
            call('api.test'),
            call(
                'chat.postMessage',
                text=expected_slack_msg,
                channel=expected_channel,
                icon_emoji=':robot_face:',
            ),
        ]
        # pass `any_order=True` as there are two implicit calls to __getitem__
        # made when checking the `ok` field of the response
        mock_sc.assert_has_calls(calls, any_order=True)


class IndeedAPITestCase(unittest.TestCase):
    """Test case for the Indeed API."""
    @classmethod
    def setUpClass(cls):
        cls.params = {
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
        cls.sampledb_path = os.path.join(TEST_DB_DIR, '.sampledb_alt.json')
        cls.raw_response_path = os.path.join(TEST_DB_DIR, '.rawresponseshort.json')

        with open(cls.raw_response_path, 'r') as f, open(cls.sampledb_path, 'r') as g:
            cls.rawdb = json.load(f)
            cls.db = json.load(g)

        cls.dbs = json.dumps(cls.rawdb)

    @patch('urllib.request.urlopen')
    def test_good_indeed_request(self, mock_urlopen):
        """Test that we get a good response for a good API call."""
        instance = mock_urlopen.return_value.__enter__.return_value
        instance.read.return_value = self.dbs.encode('utf-8')
        all_posts = indeed_api_request(self.params)
        self.assertEqual(
            self.db,
            {k: v for d in all_posts for k, v in d.items()},
        )

    @patch('urllib.request.urlopen')
    def test_malformed_json_response(self, mock_urlopen):
        """Test that we get a good response for a good API call."""
        malformed_response = self.dbs[:-1]
        instance = mock_urlopen.return_value.__enter__.return_value
        instance.read.return_value = malformed_response.encode('utf-8')

        with self.assertRaises(json.decoder.JSONDecodeError):
            all_posts = indeed_api_request(self.params)
            # exception won't be raised until we iterate the generator
            next(all_posts)

    @patch('urllib.request.urlopen')
    def test_indeed_bad_publisher_key(self, mock_urlopen):
        """Test that we raise for a bad publisher key."""
        # {'error': 'Invalid publisher number provided.'}
        expected_response = '{"error": "Invalid publisher number provided."}'
        instance = mock_urlopen.return_value.__enter__.return_value
        instance.read.return_value = expected_response.encode('utf-8')

        with self.assertRaises(IndeedAuthenticationError):
            all_posts = indeed_api_request(self.params)
            # exception won't be raised until we iterate the generator
            next(all_posts)


if __name__ == '__main__':
    unittest.main()
