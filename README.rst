###########
Job Notify
###########

``jobnotify`` is a command-line utility to help alert you to new job postings.

.. note:: This project requires Python >= 3.6.0


Installation
=============

.. note:: It is recommended to install this application in a virtual environment.

The easiest way to install this project is via ``pip``::

    $ pip install jobnotify

Alternatively, you can clone the repository to get the `source code
<https://github.com/matthewmckenna/jobnotify>`_.

::

    $ git clone https://github.com/matthewmckenna/jobnotify.git
    $ cd jobnotify
    $ pip install .

This will ensure that the application is set up correctly.


Prerequisites
==============

Indeed
-------

#. Sign up for an `Indeed Publisher account`_ and log in.
#. Click on the ``Job Search API`` tab. Under ``Sample Request`` section you
   will find your ``publisher ID``. Take note of this key, as you will need it
   later.

Gmail
------
To receive notifications via email, you will need a `Gmail account`_ to send
the emails.

While it may be possible to use an existing Gmail account to both send and
receive the emails, this option has not been tested. This option also comes with
a downside in that your password to this account will be stored in plaintext on
your machine. If this is your primary account this is certainly not desirable.

I recommend setting up a new account to send the notification emails. This is a
quick process and the account can be used in future for other notification tasks.
Now, we will quickly set up an ``App password`` for this application.

#. When you have set up your account, click on your avatar in the top-right, and
   navigate to ``My Account``.
#. Under ``Sign-in & security`` click on the ``Signing into Google`` link.
#. Click on ``App passwords``.
#. Generate a password and take note of this. This will be needed when
   configuring ``jobnotify``.

Slack
------
If you wish to receive job notifications via Slack, then please follow the
instructions in `Slack Configuration`_.

Configuration
==============

Your configuration file for ``jobnotify`` will be located in ``~/.jobnotify``,
and will be named ``jobnotify.config``.

The quickest way to get a skeleton configuration file is by running the
application with the ``-c`` or ``--config`` flag as follows:

.. code-block:: sh

    $ jobnotify --config

The will set-up the ``.jobnotify`` application data directory in your home
directory.

You will need to edit the ``jobnotify.config`` file and fill out valid values.
Terms in brackets ``[]`` are sections. There are a number of required fields
for each section, detailed below:

``[indeed]`` section
---------------------
==============  ======================================================================
Key             Description
==============  ======================================================================
``key``         Indeed API Publisher Key
``location``    Location/city to search - e.g., ``dublin``.
``country``     Country code to search - e.g., ``ie`` for Ireland, ``gb`` for
                the United Kingdom.
``query``       Job search term - e.g., ``data scientist``.
==============  ======================================================================


``[email]`` section
---------------------
===============  ================================================================
Key              Description
===============  ================================================================
``email_from``   Email address of account which will send notification.
``password``     Password of account which will send notification.
``email_to``     Recipient email address.
===============  ================================================================

Optional parameters
^^^^^^^^^^^^^^^^^^^^

These optional keys are included under the ``email`` section.

================  ================================================================
Key               Description
================  ================================================================
``name``          Recipient first name (used only to personalise email message).
``sender_name``   Name for account sending the email, e.g., ``Job-Notify``.
``signature``     Sign-off used in email message.
================  ================================================================


``[slack]`` section
--------------------

More detail can be found in the `Slack Configuration`_ document.

============  ================================================================
Key           Description
============  ================================================================
``token``     Slack token for your bot.
``channel``   Name of the Slack channel to post to. You must also include
              the ``#``, e.g., ``#jobs``.
============  ================================================================


``[notify_via]`` section
-------------------------

The values for the keys below should be ``true`` or ``false``. Note that at
least one option must be set ``true`` below.

==========  =================================
Key         Description
==========  =================================
``email``   Send notifications via email.
``slack``   Send notifications via Slack.
==========  =================================


Usage
======

Before running ``jobnotify``, make sure that you have followed the instructions
under the `Prerequisites`_ and `Configuration`_ sections above.

To run simply execute the following:

.. code-block:: sh

    $ jobnotify

To run this application automatically, one can use a ``cron job``. To edit your
``crontab`` file, execute the following:

.. code-block:: sh

    $ crontab -e

Say for example, you wished to run the application four times a day, at 09:00,
13:00, 18:00 and 22:00. Your ``crontab`` entry would resemble the following::

    * 9,13,18,22 * * * /home/matthew/miniconda3/envs/jn/bin/jobnotify

In the example above, note that I have provided the full path to the ``jobnotify``
application. In the case above, I had ``pip install``ed  ``jobnotify`` to a
new virtual environment named ``jn``. To find the full path to the application
you can run:

.. code-block:: sh

    $ which jobnotify

from your terminal.


Options
=====================

If you wish to manually run the application, there are some command-line options
available, detailed below:


-v, --verbose  Turn on logging to file. This will output a file named
               ``.jobnotify.log`` in your current directory.
-c, --config  Used to create the ``.jobnotify`` application data directory and
              sample configuration file.
-f FILE, --file=FILE  Path to alternate configuration file. Defaults to
                      ``~/.jobnotify/jobnotify.config``

Troubleshooting
================

If you encounter any issues, please carry out the following:

#. Run the application with the ``-v`` or ``--verbose`` flag. This will create
   a log file in your current directory named ``.jobnotify.log``.
#. Capture any output from your terminal and add to a text file.

Create an issue and attach both files.


.. _Indeed Publisher account: https://secure.indeed.com/account/register
.. _Gmail account: https://accounts.google.com/SignUp?hl=en
.. _Slack Configuration: https://github.com/matthewmckenna/jobnotify/blob/master/docs/slack_config.rst
