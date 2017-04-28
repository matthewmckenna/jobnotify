#!/usr/bin/env python3
from configparser import DuplicateOptionError
import email
import json
import logging
import os
import re
import smtplib
import sys
from urllib.parse import urlencode
import urllib.request

from slackclient import SlackClient

from .exceptions import (
    ConfigurationFileError,
    EmailAuthenticationError,
    IndeedAuthenticationError,
    SlackCfgError,
)
from .utils import (
    get_sanitised_params,
    get_section_configs,
    initial_setup,
    load_json_db,
    process_args,
    write_json_db,
)

INDEED_BASE_URL = 'http://api.indeed.com/ads/apisearch'
INDEED_API_LIMIT = 25
DB_DIR = os.path.join(os.path.expanduser('~'), '.jobnotify', 'databases')
PATH_TO_CFG = os.path.join(os.path.expanduser('~'), '.jobnotify', 'jobnotify.config')


def build_url(base_url, params):
    """Return a correctly formatted URL.

    Args:
        base_url: base URL of the API
        params: dictionary of parameters to be encoded.

    Returns:
        URL string
    """
    encoded_params = urlencode(params)
    return f'{base_url}?{encoded_params}'


def construct_slack_message(posts):
    """Construct a Slack message for sending.

    The Slack RTM API (https://api.slack.com/rtm#limits)
    recommends that a single message be no longer than 4 kB.
    To handle this, we construct our message, and then
    subsequently split into messages of 10 listings or less.

    An iterable is returned: either a single element list
    containing a message with <= 10 listings, or a
    generator with > 10 listings.

    Args:
        posts: dictionary containing new job listings.

    Returns:
        msg_it: an iterable containing the message(s) to
            be posted. Note this may be a single element
            list or a generator.
    """
    nposts = len(posts)

    # build the full message
    msg_template = '{}. <{url}|{jobtitle} @ {company}>\nSnippet: {desc}\n'
    msg = '\n'.join(msg_template.format(i+1, **p) for i, p in enumerate(posts.values()))

    if nposts > 10:
        logging.debug('Splitting message into %d chunks..', (nposts//10)+1)
        # split the message after 10 listings, i.e., on a `11.`, `21.`, etc.
        t = [''] + re.split(r'(\d?\d1\.)', msg)
        # create an iterator from the above list
        it = iter(t)
        # create a generator which pairs successive elements of the original list
        msg_it = (m+next(it, '') for m in it)
    else:
        msg_it = [msg]

    return msg_it


def construct_email(cfg, query, location, posts):
    """Construct an email message.

    Args:
        cfg: email configuration.
        query: search term used.
        location: location to search for jobs.
        posts: dictionary containing new job listings.

    Returns:
        message: string containing the email message.
    """
    nposts = len(posts)

    # unpack required variables
    user, send_to = cfg['email_from'], cfg['email_to']

    # unpack optional variables
    try:
        name = cfg['name']
    except KeyError:
        # if the `name` key isn't present, then use the first part of the
        # email address to address recipient.
        name = cfg['email_to'].split('@')[0]

    try:
        sender_name = cfg['sender_name']
    except KeyError:
        sender_name = cfg['email_from']

    try:
        signature = cfg['signature']
    except KeyError:
        signature = ''

    # some temporary variables to correct grammar in the email message
    was_were = 'was' if nposts == 1 else 'were'
    is_are = 'is' if nposts == 1 else 'are'
    job_s = 'job' if nposts == 1 else 'jobs'
    listing_s = 'listing' if nposts == 1 else 'listings'

    subject = f'Job opportunities: {nposts} new {job_s} posted'
    description = '{}. {jobtitle} @ {company}\nLink: {url}\nLocation: {location}\nSnippet: {desc}\n'
    posts_content = '\n'.join(description.format(i+1, **p) for i, p in enumerate(posts.values()))

    s = (
        f'From: {sender_name} <{user}>\n'
        f'To: {send_to}\n'
        f'Subject: {subject}\n'
        f'Hello {name},\n\n'
        f'There {is_are} {nposts} new job {listing_s} to review.\n'
        f'The following job {listing_s} {was_were} found for {repr(query)} in {repr(location)}:\n\n'
        f'{posts_content}\n'
        f'{signature}'
    )

    return s


def indeed_api_request(params):
    """Performs an API request and returns results.

    Args:
        params: dictionary with search parameters.

    Returns:
        posts: a generator containing dictionaries.

    Raises:
        json.decoder.JSONDecodeError: may be raised if we
            get a malformed response from the API.
    """
    complete_result = False

    while not complete_result:
        url = build_url(INDEED_BASE_URL, params)

        with urllib.request.urlopen(url) as u:
            r = u.read().decode('utf-8')

        response = json.loads(r)

        if 'error' in response:
            raise IndeedAuthenticationError('Invalid Indeed publisher key provided.')

        for result in response['results']:
            yield {
                result['jobkey']:
                    {
                        'jobtitle': result['jobtitle'],
                        'company': result['company'],
                        'date_created': result['date'],
                        'location': result['formattedLocation'],
                        'url': result['url'].split('&')[0],
                        'lat': result['latitude'],
                        'lon': result['longitude'],
                        'desc': result['snippet'],
                    }
                }

        if response['end'] >= response['totalResults']:
            complete_result = True

        # update results start in order to get to the next page
        params['start'] += INDEED_API_LIMIT


def email_notify(cfg, posts, query, location):
    """Notify recipient of new postings.

    Args:
        cfg: email section from configuration file.
        posts: new posts since the last notification
        query: query from `indeed` section of config file
        location: location from `indeed` section of config file
    """
    user = cfg['email_from']
    password = cfg['password']

    message = construct_email(cfg, query, location, posts)
    msg = email.message_from_string(message)
    msg.set_charset('utf-8')

    try:
        send_email(user, password, msg)
    except smtplib.SMTPAuthenticationError as e:
        raise EmailAuthenticationError(
            'Email authentication error. Please check entries for `email_from` '
            'and `password` in your configuration file.'
        )


def send_email(user, password, msg):
    """Send an email.

    Args:
        user: account of sender
        password: password of sender
        msg: email.message.Message object

    Raises:
        smtplib.SMTPAuthenticationError:
            535, b'5.7.8 Username and Password not accepted.
    """
    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.ehlo()  # success 250
        smtp.starttls()  # success 220
        smtp.login(user, password)  # success 235 smtplib.SMTPAuthenticationError
        smtp.send_message(msg)  # empty dict is a success


def slack_notify(cfg, posts):
    """Post a message to a Slack channel.

    Args:
        cfg: configuration for Slack account.
        msg_it: message(s) to be sent. May be a list
            or a generator.

    Raises:
        SlackCfgError: raised if we get a bad response.
    """
    msg_it = construct_slack_message(posts)

    token = cfg['token']
    channel = cfg['channel']

    sc = SlackClient(token)

    # https://api.slack.com/methods/chat.postMessage
    # slack_errors = {
    #     'not_authed': 'No authentication token provided.',
    #     'invalid_auth': 'Invalid authentication token.',
    #     'account_inactive': 'Authentication token is for a deleted user or team.',
    #     'no_text': 'No message text provided',
    #     'not_in_channel': 'Cannot post user messages to a channel they are not in.',
    #     'channel_not_found': 'Value passed for channel was invalid.',
    # }

    r = sc.api_call('api.test')
    if not r['ok']:
        reason = r['error']
        raise SlackCfgError(f'ERROR: {reason}')

    for m in msg_it:
        sc.api_call(
            'chat.postMessage',
            text=m,
            channel=channel,
            icon_emoji=':robot_face:',
        )


def jobnotify(cfg_filename=PATH_TO_CFG, database_dir=DB_DIR):
    """Main entry point for the script"""
    # TODO: if config does not exist perhaps populate with defaults
    if not os.path.isfile(cfg_filename):
        raise FileNotFoundError(f'Configuration file {repr(cfg_filename)} does not exist.')

    # load all configuration files
    cfgs = get_section_configs(cfg_filename)

    # the `indeed` section is the first section in the list
    indeed_cfg = cfgs[0]

    params = {
        'publisher': indeed_cfg['key'],  # publisher ID
        'q': indeed_cfg['query'],  # query
        'l': indeed_cfg['location'],  # location (city, state, region)
        'radius': indeed_cfg['radius'],  # distance from search location 'as the crow flies'
        'jt': 'fulltime',  # job-type: 'fulltime', 'parttime, 'contract', 'temporary', 'internship'
        'limit': 25,  # max number of results per query - max 25
        'fromage': 10,  # number of days back to search
        'start': 0,  # start results at this search number
        'highlight': 0,  # bold search term in snippet
        'latlong': 1,  # return latitude and longitude
        'co': indeed_cfg['country'],  # search within this country
        'v': 2,  # version of the API - should be 2
        'format': 'json',  # response format
    }

    logging.debug(params)

    query, loc = get_sanitised_params(params['q'], params['l'])

    db_name = f'{query}_{loc}.json'
    db_path = os.path.join(database_dir, db_name)
    db = load_json_db(db_path)
    logging.info('Load JSON database %r', db_path)

    # get all listings from the indeed API
    all_posts = indeed_api_request(params)

    # build a list of posts that we haven't seen before
    posts = {k: v for d in all_posts for k, v in d.items() if k not in db}
    logging.info('len(posts)=%d', len(posts))

    if posts:
        # send the notification
        notify(cfgs, posts)

        # update our existing database
        db.update(posts)

        logging.info('Write JSON database %r', db_path)

        write_json_db(db, db_path)
    else:
        logging.info('No new positions since last notification.')


def notify(cfgs, posts):
    """Generic notification function."""
    # assuming cfgs is a list of configs
    # if someone modifies the layout of the cfg file we're in trouble!
    indeed, email, slack, notify_via = cfgs

    if notify_via.getboolean('slack'):
        slack_notify(slack, posts)
        logging.info('Slack message sent with %d listings(s)', len(posts))

    if notify_via.getboolean('email'):
        query = indeed.get('query')
        location = indeed.get('location')
        email_notify(email, posts, query, location)
        logging.info('Email sent with %d listings(s).', len(posts))



def main():
    """Main entry point for this utility."""
    app_data_dir = os.path.join(os.path.expanduser('~'), '.jobnotify')

    # process command line arguments
    # if no command line args are passed sys.argv[1:] == []
    args = process_args(sys.argv[1:])

    if args.config:
        initial_setup(app_data_dir)
        print(f'App data directory created: {app_data_dir}')
        sys.exit()

    if args.verbose:
        # setup basic logging to file
        logging.basicConfig(
            filename=f'.{os.path.splitext(os.path.basename(__file__))[0]}.log',
            format='%(asctime)s %(message)s',
            level=logging.DEBUG
        )
    else:
        # disable logging
        logging.disable(logging.CRITICAL)

    logging.debug('args: %r', args)

    # if the app data directory has not been set up before then do this now
    if not os.path.isdir(app_data_dir):
        initial_setup(app_data_dir)
        logging.info('Created app data directory: %r', app_data_dir)

    try:
        jobnotify(args.file, DB_DIR)
    except (
            ConfigurationFileError,
            DuplicateOptionError,
            FileNotFoundError,
            json.decoder.JSONDecodeError,
            ) as e:
        print(f'ERROR: {e}')
        logging.exception(e)


if __name__ == '__main__':
    sys.exit(main())
