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
        task_summary.txt - contains a text summary of the task
        activity.json - contains all comments and status changes


HOW TO RUN
----------

1. Enter the value of your 'SACSID' cookie into 'sacsid_cookie.txt'.
   (Log into the GCI website and examine your cookies using your
   browser's inspection or web development features.)

2. $ python gciq.py --apikey <your api key>
   (Log into the GCI website and find your API key under User Profile)


FLAGS
-----
--apikey is used to input your apikey
--datadir is used to specify a different output directory


TODO
----
* stash instances by status
* tally instances apriori
* stash raw html


Development and contributions by:
  Jeff Sieu (original author)
  Christopher Sean Morrison <morrison@brlcad.org>
