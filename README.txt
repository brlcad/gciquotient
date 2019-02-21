GCI Quotient
============

This script downloads Google Code-In (GCI) data.  This includes task
descriptions and claimed task instance data, including uploaded files.

Everything is stashed by default into a 'gci_data' subdirectory.
Tasks are stored in gci_data/tasks while instance data is saved into
per-instance subdirectories named according to timestamp and title.

  gci_data/
    tasks/ - contains all tasks in json format
    instances/ - contains all task instances
      DATE-TASK_NAME_-_ORG/ - contains a single task instance
        instance.txt - contains a text summary of the task
        instance.json - contains raw instance data
        activity.json - contains all comments and status changes


HOW TO RUN
----------

0. Install the necessary prerequisites:
   python 2.7+
   pip install requests[security]

1. Enter the value of your 'SACSID' cookie into 'sacsid_cookie.txt'.

   (Log into the GCI website and examine your cookies using your
   browser's inspection or web development features.)
   Instructions for Chrome : 
   1. Log into the GCI Website
   2. Chrome Controls (Top-right) --> Settings --> Advanced --> Content Settings --> Cookies --> See all cookies...
   3. Search for 'codein.withgoogle.com' --> SACSID --> Copy Content (~AJKiYcG...) to sacsid_cookie.txt

2. $ python gciq.py --apikey <your api key>

   (Log into the GCI website and find your API key under User Profile)


RUNNING TIPS
------------

If instance downloading is interrupted, GCI Quotient will pick up
where it left off the next time it's run.  If you don't want that,
delete your datadir or specify a new datadir.

Empty activity.json files (i.e., containing just []) can happen when
your session cookie has expired or was renewed.  Check your browser to
get the new value.


FLAGS
-----
--apikey is used to input your apikey
--datadir is used to specify a different output directory


TODO
----
* stash instances by status
* tally instances apriori
* stash raw html
* skip client.GetTask during instances
* close streams we're done with

Development and contributions by:
  Jeff Sieu (original author)
  Christopher Sean Morrison <morrison@brlcad.org>
