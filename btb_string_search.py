# A script using the functions from the rdrsrch_fxns.py module to output a table
# documenting usage of rdrobust in the do and R files of a certain set of DOIs

from btbsrch_fxns import *
import getpass as gp

username = gp.getpass('Username:')
password = gp.getpass('Password:')
URLs = getURLs(username, password, 'aeaverification')
repos = cloneRepos(URLs)
new_counts = stringOccurrences(repos)
update_str_counts(new_counts)
update_checked_URL(repos)
