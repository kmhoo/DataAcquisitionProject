__author__ = 'griffin'

import urllib2
from bs4 import BeautifulSoup
import re
import random
import time
import json
import csv


def URLrequest(name):
    """

    :param name:
    :return:
    """

    try:
        name = urllib2.quote(name)
        base = 'http://www.simplyhired.com'
        url = base+name
        header = {'User-Agent':'Magic Browser'}
        request = urllib2.Request(url, headers=header)
        print request.get_full_url()

        try:
            page = urllib2.urlopen(request)
            #print 'Querying...' + url
        except urllib2.URLError, e:
            print 'Failed to reach URL'
            #print e.read()
            wait_time = round(max(0, 1 + random.gauss(0,0.5)), 2)
            time.sleep(wait_time)
            try:
                print 'Trying again...'
                page = urllib2.urlopen(request)
            except urllib2.URLError, e:
                if hasattr(e, 'reason'):
                    print 'Failed to reach url'
                    print 'Reason: ', e.reason
                    return None
                elif hasattr(e, 'code'):
                    if e.code == 404:
                        print 'Error: ', e.code
                        return None
            else:
                content = page.read()
                soup = BeautifulSoup(content, 'lxml')
                return soup
        else:
            content = page.read()
            soup = BeautifulSoup(content, 'lxml')
            return soup

    except KeyError:
        return None


def getAllTitles(ext):
    """
    Function to obtain all of the job titles provided by Simply Hired
    :param ext: extension to append to base Simply Hired URL for querying
    :return: list of job titles
    """

    # Obtain html using Beautiful Soup
    soup = URLrequest(ext)

    # Initialize
    alphaURLs =[]
    allTitles = []

    # Find all nodes with links to alphabetically categorized job titles
    alphaNodes = soup.find_all('a', {'class': re.compile('^header_letter_\w+')})

    # For each alphabet node, get the link
    for a in alphaNodes:
        alphaURLs.append(a.get('href'))

    # For each alphabet URL, obtain the html and and find all of the
    # job title nodes, with the job title in the text
    for a in alphaURLs:
        wait_time = round(max(1, 1.5 + random.gauss(0,1)), 2)
        time.sleep(wait_time)
        soup = URLrequest(a)
        jobNodes = soup.find_all('a', {'class': 'data-cell-link one-line'})
        for j in jobNodes:
            allTitles.append(j.text)

    # Return list of titles
    return allTitles


def getSalary(title):
    """
    Function to find the average annual salary for a job title on Simply Hired
    :param title: job title to find a salary for
    :return:
    """

    # Construct the URL extension to append to base Simply Hired URL for querying
    title = re.sub(" ", "-", title)
    ext = '/salaries-k-' + title + "-jobs.html"

    # Get html using beautiful soup
    soup = URLrequest(ext)

    # Return nothing if page doesn't exist
    if soup is None:
        return ""

    # Find salary and return text if it exists
    salary = soup.find('span', {'class': 'SH_salary'})
    if salary is None:
        return ""
    else:
        return salary.text


def main():

    start = time.time()

    titles = getAllTitles('/job-search/title')
    salaries = {}

    # for title in titles:
    #     wait_time = round(max(1, 1.5 + random.gauss(0,1)), 2)
    #     time.sleep(wait_time)
    #     salaries[title] = getSalary(title)
    #     print salaries[title]

    for i in xrange(len(titles)):
        salaries[i] = {"Title": ""}


    with open("SimplyHired_JobSalaries.json", 'wb') as out_file:
        json.dump(salaries, out_file)

    end = time.time()

    print "Time Elapsed: " + str(end-start)

def exportCSV(json_file):
    x = json.load(open(json_file))
    file = open("SimplyHired_JobSalaries.csv", "wb+")
    f = csv.writer(file)
    f.writerow(["Job", "Average National Salary"])
    for x in x:
        f.writerow(x.keys(), x.values())


main()
exportCSV('SimplyHired_JobSalaries.csv')