This script will download all the GCI task instance's data.  This includes uploaded files!  Instance data is saved to a text file named 'task_information.txt' while uploaded files are prefixed.  Data is saved into a subdirectory named according to timestamp and title.

HOW TO RUN
----------
1. Enter the value of your 'SACSID' cookie into 'sacsid_cookie.txt', sans newline.
   (Log into the GCI website and examine your cooies via Web or Storage Inspector)
2. Change directory to the folder containing these files.
3. $ python gciq.py --apikey <your api key>

The instance folders will be created in the same directory as the gciq.py file.

FLAGS
-------
--apikey is used to input your apikey
--debug can be added for debugging use.


Development and contributions by:
  Jeff Sieu (original author)
  Christopher Sean Morrison <morrison@brlcad.org>
