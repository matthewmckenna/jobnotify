###########
Job Notify
###########

``jobnotify`` is a command-line utility to help alert you to new job postings.

.. note:: This project requires Python >= 3.6.0


Installation
=============

The easiest way to install this project is via ``pip``::

    $ pip install git+https://github.com/matthewmckenna/jobnotify

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
Sign up for an `Indeed Publisher account`_ and log in.
Click on the ``Job Search API`` tab.
Under ``Sample Request`` section you will find your ``publisher ID``. Take note
of this key, as you will need it later.

Email
------
In order to receive notifications, you will need to set up an email account to
send the emails.

You can use an existing email address to do both the sending and the receiving,
but this would mean storing an account password for a primary account in a
configuration file. Anyone with access to the config file would have access
to your primary account, which is not desirable.

For this tutorial, I set up a new `Gmail account`_ to send the notification
emails.


Configuration
==============

#. Make a copy of the file ``jobnotify.config.sample`` and rename the copy to
   ``jobnotify.config``.
#. Under the ``indeed`` section, fill out the fields for ``location``,
   ``country`` and ``query``.
#. Under the email section, fill out the fields for ``email_from``, ``email_to``
   and ``password``.

Optionally, you can uncomment the following fields, though they are not required:

- ``name``
- ``sender_name``
- ``signature``

Each of these fields are detailed below:

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

Optional parameters:

================  ================================================================
Key               Description
================  ================================================================
``name``          Recipient first name (used only to personalise email message).
``sender_name``   Name for account sending the email, e.g., ``Job-Notify``.
``signature``     Sign-off used in email message.
================  ================================================================


Usage
======

Before running ``jobnotify``, make sure that you have followed the instructions
under the `Prerequisites`_ and `Configuration`_ sections above.

Additionally, for the time being, you must be in the ``jobnotify`` directory
when running this application. The configuration file the application attempts
to use is relative to the directory the application was run from.

To run, navigate to the ``jobnotify`` directory and simply execute the following:

.. code-block:: sh

    $ jobnotify

To run this application automatically, one can use a ``cron job``. To edit your
``crontab`` file, execute the following:

.. code-block:: sh

    $ crontab -e

Then, to run this application at 09:00, 13:00, 18:00 and 22:00 every day, add
the following line to your ``crontab``, replacing ``/home/matthew/jobnotify/``
with the your own path to the ``jobnotify`` directory::

    * 9,13,18,22 * * * /home/matthew/jobnotify/jobnotify


Known Issues
=============

- It is necessary to run the application from the ``jobnotify`` directory.
- ``jobnotify.config`` must be present in the current directory.

Experimental Features
======================

Slack Notifications
--------------------
Slack notifications have not yet been thoroughly tested. However, if you wish
to enable Slack notifications, follow the instructions in the `Slack
Configuration`_ section of the docs.


.. _Indeed Publisher account: https://secure.indeed.com/account/register
.. _Gmail account: https://accounts.google.com/SignUp?hl=en
.. _Slack Configuration: https://github.com/matthewmckenna/jobnotify/blob/master/docs/slack_config.rst
