####################
Slack Configuration
####################

In order to receive notifications via Slack, there is some additional setup
that is needed.

You will need:

#. A `Slack`_ team.
#. An appropriate channel to post messages to.
#. A Slack Bot User OAuth Access Token.

Setup
======
#. Head over to https://slack.com/ to create a new Slack team, or sign-in if you
   already have an account.
#. With your team set up, you will now need to `create an App`_. Enter an
   ``App Name`` and from the dropdown menu and select the team the App will be
   associated with.
#. Under ``Add features and functionality``, selct the ``Bots`` button. Click
   on the ``Add a Bot User`` button. Choose a username and click the green
   ``Add Bot User`` button.
#. Navigate back to the ``Basic Information`` page. Under ``Building Apps for
   Slack`` expand the ``Install your app to your team`` section and click the
   ``Install App to Team`` button. Authorise the App on the next page.
#. On the left navigation pane, under ``Features`` click ``OAuth & Permissions``.
   Copy the ``Bot User OAuth Access Token`` by clicking on the ``Copy`` button.
   You will need this to authenticate your bot.
#. Open your ``jobnotify.config`` file. Under the ``[slack]`` section populate
   the value for the ``token`` key with the value you just copied. It should
   start with ``xoxb-``.
#. We're almost finished! Head over to the channel you wish the bot to post on.
   You can now invite the bot to the channel using ``/invite`` slash command.
   For example, ``/invite @jobnotifybot``. You should see that your bot has
   joined the channel.


Configuration
==============

You will now need to populate the keys under the ``[slack]`` section in your
``jobnotify.config`` file. You should populate ``token`` and ``channel``.

Under the ``[notify_via]`` you should set ``slack`` to ``true``.


.. _Slack Developer Kit for Python: https://github.com/slackapi/python-slackclient
.. _Slack API: https://api.slack.com/
.. _Slack: https://slack.com/
.. _Slack Bot Users: https://api.slack.com/bot-users
.. _create an App: https://api.slack.com/apps?new_app=1
