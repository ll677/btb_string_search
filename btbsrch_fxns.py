# functions for the btb_string_search script

import os
import git
import numpy as np
import pandas as pd
import re
import datetime as dt
import shutil
from bitbucket.client import Client


##### SCRIPT FUNCTIONS #####

def getURLs(username, password, owner,strlist):
    """
    Returns a list of tuples of bitbuckets URLs and last_updated time that we
    want to clone. Also, generate a checked_URL.csv file that stores the URLs
    and last_updated time for each URL. If last_updated time of a URL is before the last modified time we got from bitbucket website, we append a tuple of URL and last_modified time of that URL, otherwise we will just skip this URL because we have already checked it before.
	
    Parameters:
        username: email address to login to bitbucket
        password: password to login to bit bitbucket
        owner: owner of bitucket repo, i.e. aeaverification in this case
        strlist: list of strings needed to be searched

    Returns:

        URLs: dict; URLs of repos to clone index tuples.  0 index is string date of last update, 1 index is string name of repo
    """
    URLs = {}
# change to "checked_URL_empty.csv" if you want to start from fresh
    df = pd.read_csv("checked_URL.csv")

    checked_URLs = list(df['URL'])
    checked_URLs_time = list(df['last_updated_time'])
    client = Client(str(username), str(password), str(owner))
    checked_strs=list(df['last_checked_strings'])

    # alt soln. here: https://thepythoncoding.blogspot.com/2019/06/python-script-to-clone-all-repositories.html?fbclid=IwAR0a-cI-EI9cA1cgQGkiXCY9R6-5SrJq_NItKurEQ59eSVnzGCVpmKtWs7g

    # compile repo list
    pg = 1
    d = [0]
    repos = []
    while len(d) > 0:
        d = client.get_repositories(
            params={'pagelen': 100, 'page': pg})['values']
        repos = repos+d
        pg += 1

    # get repo URLs

    for repo in repos:
        links = repo['links']
        clone = links['clone']
        raw_URL = clone[0]['href']

        # remove user handle from url
        hst = raw_URL.find('//')+2
        hend = raw_URL.find('bitbucket.org')
        URL = raw_URL[:hst]+raw_URL[hend:]
        upd_time = repo['updated_on']
        name = repo['name']
        if URL in checked_URLs:
            ind = checked_URLs.index(URL)
            old_time = checked_URLs_time[ind]
            urlchecks=checked_strs[ind].split(',')
            not_chkd=False
            for tochk in strlist:
                not_chkd=not_chkd or (not (tochk in urlchecks))
            if not_chkd or parseTime(old_time) < parseTime(upd_time):
                URLs[URL] = (upd_time, name)
        else:
            URLs[URL] = (upd_time, name)
    return URLs


def cloneRepos(URLs):
    """
    Clones the repos corresponding to the links in URLs into the a subdirectory
    named repos of the current working directory. May require manual login.

    Inputs:

        URLs: dict; URLs of repos to clone index tuples, 0 index is string date
            of last update, 1 index is string name of repo

    Returns:

        repos: a dictionary indexing the repos' URLs to a tuple of their repo object (0),
            last update time (1), and DOI if present (2) ('' if not present)


    """

    repos = {}

    # create and navigate to new directory repos

    try:
        os.mkdir('repos')
    except FileExistsError:
        pass

    current_dir = os.getcwd()

    os.chdir('repos')

    # add repos to folder named repos

    for url in URLs.keys():

        print('cloning '+str(url))
        upd = URLs[url][0]
        name = URLs[url][1]
        DOI = findDOI(name)

        # git clone if directory doesn't exist

        try:
            r = git.Repo.clone_from(url, os.getcwd()+'\\'+name)
            repos[url] = (r, upd, DOI)

        except:

            # try git pull if directory already exists

            try:
                print('try to pull'+str(os.getcwd()+'\\'+name))
                r = git.Repo(os.getcwd()+'\\'+name)
                o = r.remotes.origin
                o.pull()
                repos[url] = (r, upd, DOI)

            #encount empty uniniciated repo
            except:
                print('just continue:'+str(os.getcwd()+'\\'+name))
                r = git.Repo(os.getcwd()+'\\'+name)
                repos[url] = (r, upd, DOI)
                continue

    # navigate back to original directory

    os.chdir(current_dir)

    return repos


def stringOccurrences(repos,strlist):
    """
    Input:

        repos: a dictionary indexing the repos' URLs to a tuple of their repo object (0),
            last update time (1), and DOI if present (2) ('' if not present)
        strlist: list of strings to search
		filetypes: list of strings of filename endings to check; i.e. ['.R','.do'] to check for R and do files

    Returns:

        new_counts: A pd.DataFrame (index are URLs, col 1 is DOI if extractable, rest of cols are string occurences)
    """

    new_counts = pd.DataFrame(index=pd.core.indexes.base.Index([], name='URL'),
                              columns=['DOI']+strlist)
    URLs = repos.keys()
    for url in URLs:
        new_counts.at[url,'DOI']=repos[url][2]
        ct = 0
        paths = getFilePaths(repos[url][0].working_dir,filetypes)
        for s in strlist:
            for f in paths:
                file = open(f, 'r', errors='ignore')
                text = file.read()
                file.close()
                ct += count_strs(text,s)
            if ct > 0:
                new_counts.at[url,s] = ct

    return new_counts


def update_str_counts(new_counts):
    """
    Updates string_counts.csv in current working directory with info in new_counts. Includes
    entries for new repos and replaces entries for old repos which have been modified.

    Input:

        new_counts: A pd.DataFrame (index are URLs, col 1 is DOI if extractable, rest of cols are string occurences)

    """
    old_counts = pd.read_csv('string_counts.csv', index_col='URL')
    old_counts.update(new_counts[new_counts.index.isin(old_counts.index)])
    str_counts = old_counts.append(
        new_counts[~new_counts.index.isin(old_counts.index)])
    str_counts.to_csv('string_counts.csv')


def update_checked_URL(repos,strlist):
    """
    Updates checked_URL.csv with the URLs and last modified date of repos examined in this
    run of the script as well as what strings were searched for

    Input:

        repos: a dictionary indexing the repos' URLs to a tuple of their repo object (0),
            last update time (1), and DOI if present (2) ('' if not present)
        strlist: list of strings which were searched for
    """
    checked_URL = pd.read_csv('checked_URL.csv', index_col='URL')
    for url in repos.keys():
        checked_URL.at[url] = {'last_updated_time': repos[url][1],'last_checked_strings':','.join(strlist)}
    checked_URL.to_csv('checked_URL.csv')


##### HELPER FUNCTIONS #####

# getURLs helpers

def parseTime(s):
    """
    Input:

        s: a string representing a date and time in the form:
            <YYYY>-<MM>-<DD>T<hh>:<mm>:<ss>.<ssssss>+00:00

    Returns:

        t: a datetime object representing the date and time given by s
    """
    # print(s)
    hyp1 = s.find('-')
    hyp2 = s.find('-', hyp1+1)
    Tpos = s.find('T')
    col1 = s.find(':')
    col2 = s.find(':', col1+1)
    plus = s.find('+')

    year = int(s[:hyp1])
    month = int(s[hyp1+1:hyp2])
    day = int(s[hyp2+1:Tpos])
    hour = int(s[Tpos+1:col1])
    minute = int(s[col1+1:col2])
    seconds = int(float(s[col2+1:plus]))

    t = dt.datetime(year, month, day, hour, minute, seconds)
    return t

# cloneRepos helper


def findDOI(name):
    """
    Input:

        name: string representing name of a repo

    Returns:

        DOI: string of the repo's DOI if extractable, '' otherwise
    """
    DOI = ''
    prefEnd = name.find('10.1257')+7

    if prefEnd < 0:
        return DOI

    import string
    try:
        suffSt = re.search(str(list(string.ascii_letters)),
                           name[prefEnd:]).start()+prefEnd
        suffEnd = name.find('-', suffSt)
        if suffEnd < 0:
            suffEnd = len(name)
        DOI = '10.1257/'+name[suffSt:suffEnd]
        return DOI
    except:
        return DOI


# stringOccurrences helpers

def getFilePaths(dir,filetypes):
    """
    Input:

        dir: the path (as a string) to a directory to search
		filetypes: list of strings of filename endings to check; i.e. ['.R','.do'] to check for R and do files

    Returns:

        paths: a list of do and R filepaths contained in dir and its
            subdirectories
    """

    dirtree = os.walk(dir)
    paths = []
    for t in dirtree:
        for f in t[2]:
            if f[f.rfind('.'):] in filetypes:
                paths = paths + [os.path.join(t[0], f)]
    return paths


def count_strs(text,s):
    """
    Input:

        text: string to parse
        s: string to search for

    Returns:

        count: occurrances of string s in the text
    """

    count = sum(1 for i in re.finditer(s, text))
    return count
