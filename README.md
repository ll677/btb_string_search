# Instructions:

1. Git clone the btb_string_search repository
2. Navigate to repository in command line/terminal
3. Install all necessary packages as per requirements.md
4. Set file types to search through and list of strings to look for in btb_string_search.py
5. Run btb_string_search.py as a script (we only check new repos modified/added since last time they were checked by the script)
6. Relevant string occurence information is output as string_counts.csv, and updated time information of URLs and last checked strings stored in checked_URL.csv

# Files:
* btbsrch_fxns.py: a module containing the functions necessary to run btb_string_search
* btb_string_search.py: a script to output the report on a string's frequency in repo program files
* string_counts.csv: column A contains URLs of papers with code containing specified strings to search for, DOIs only present if extractable from repo name; other columns document the number of occurrences of strings that were searched for
* checked_URL.csv: column A contains URL of checked repo, column B contains date of repo's last update, column C contains a list of the last list of strings checked for (comma delineated)
* btbsrch_test.py: test script for btbsrch_fxns.py

# Notes:
* The script btb_string_search.py will create a directory "repos" within the working directory and clone a possibly large number of repos into it (670 at time of writing).