This script will download all the GCI task instance's data -- including files uploaded(!) -- into a text file named 'task_information.txt' and files named after their original upload, located in respective folders named after the tasks.

HOW TO RUN
----------
1. Enter the value of your 'SACSID' cookie into 'sacsid_cookie.txt', sans newline.
2. $ cd into the folder containing these 3 files.
3. $ python gciq.py --apikey <your api key>

The folders will be created in the same directory as the gciq.py file.

FLAGS
-------
--apikey is used to input your apikey
--debug can be added for debugging use.
