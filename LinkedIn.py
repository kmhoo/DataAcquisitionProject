import urllib2
from bs4 import BeautifulSoup
import re
import time
import random
import json

_lvl1 = 1
_lvl2 = 1
_lvl3 = -1

def URLrequest(name):
    """
    Attempts to request/open a linkedin.com subdomain using urllib2
    and retrieve the content using Beautiful Soup.
    :param name: extension of the URL for the subdomain
    :return: None if failed, soup if successful
    """

    try:
        name = urllib2.quote(name)
        base = 'http://www.linkedin.com'
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


def URLgen(name):
    """
    Retrieves all URLs within the linkedin.com page and determines whether
    they are further subdirectories or profiles, the returns as separate lists
    :param name: extension of the URL for subdomain
    :return: list of subdirectory URLs, list of profile URLs
    """

    url_list = []
    profile_list = []

    soup = URLrequest(name)

    if soup is not None:
        links = soup.find('ul', {'class': 'directory'})
        #print links
        urls = links.find_all('a')
        #print urls
        for i in urls:
            href = i.get('href')
            if re.match('^/directory/.*', href) is not None:
                url_list.append(href)
            elif re.match('^/pub/dir/.*', href) is not None:
                profile_list += getRepeats(href)
            elif re.match('^/pub/.*', href) is not None or re.match('^/in/.*', href) is not None:
                profile_list.append(href)

    return url_list, profile_list

def getRepeats(name):
    """
    Function to retrieve URLs for profiles within a page listing
    profiles with the same member name
    :param name: extension of the URL for subdomain
    :return: list of user profile URLs
    """

    results = []

    soup = URLrequest(name)

    if soup is not None:
        subdirectory = soup.find_all('h2')
        for sub in subdirectory:
            suburls = sub.find_all('a')
            for u in suburls:
                match = u.get('href')
                match = re.sub('^http://\w+.linkedin.com', '', match)
                results.append(match)

    return results


def getNames():
    """
    Retrieve the URLs for the primary member directories organized
    by starting character for the profiles
    :return: list of directory URLs
    """
    start_name = '/directory/people-a'

    soup = URLrequest(start_name)

    names = soup.findAll('ol', {"class": "primary"})
    nameURLs = []
    for l in names:
        a = l.findAll('a')
        for node in a:
            nameURLs.append(node['href'])
    return nameURLs


def getProfiles(name):
    """
    Finds all of the profile URLs from the given primary member directory
    by traversing the directory tree structure
    :param name: extension of the URL for primary directory
    :return: list of profile URLs
    """

    global _lvl1
    global _lvl2
    global _lvl3

    level1, profiles = URLgen(name)
    level2 = []
    level3 = []
    level4 = []

    for i in level1[0:_lvl1]:
        result, profile = URLgen(i)
        level2 += result
        profiles += profile
        wait_time = round(max(1, 1.5 + random.gauss(0,1)), 2)
        time.sleep(wait_time)

    for i in level2[0:_lvl2]:
        result, profile = URLgen(i)
        level3 += result
        profiles += profile
        wait_time = round(max(1, 1.5 + random.gauss(0,1)), 2)
        time.sleep(wait_time)

    for i in level3[0:_lvl3]:
        result, profile = URLgen(i)
        level4 += result
        profiles += profile
        wait_time = round(max(1, 1.5 + random.gauss(0,1)), 2)
        time.sleep(wait_time)

    return profiles

def getPerson(name):
    """
    Scrapes all of the relevant profile information from a profile URL
    :param name: profile URL extension
    :return: dictionary of profile information
    """

    soup = URLrequest(name)
    if soup is None:
        return {"name": "", "jobs": {}}

    name = soup.find('title').text
    name = re.sub('\| LinkedIn', '', name)

    experience = soup.find('div', {'class':'section subsection-reorder', 'id':'profile-experience'})
    if experience is None:
        jobsDict = {}
    else:
        experience = experience.find('div', {"class": "content vcalendar"})
        jobs = experience.find_all('div', {"class": re.compile("^position")})
        jobsDict = {}

        for i in range(0, len(jobs)):

            title = jobs[i].find('span', {"class": "title"})
            if title is None:
                title = ""
            else:
                title = title.text

            company = jobs[i].find('span', {"class": "org summary"})
            if company is None:
                company = ""
            else:
                company = company.text

            industry = jobs[i].find('p', {"class": re.compile('^orgstats')})
            if industry is None:
                industry = ""
            elif industry.text == '\n':
                industry = ""
            else:
                industry = industry.text
                industry = re.search('\n.+\n$', industry).group()
                industry = industry.strip()

            start = jobs[i].find('abbr', {"class": 'dtstart'})
            if start is None:
                start = ""
            else:
                start = start.text

            end = jobs[i].find('abbr', {"class": 'dtend'})
            if end is None:
                end = jobs[i].find('abbr', {"class": "dtstamp"})
                if end is None:
                    end = ""
                else:
                    end = end.text
            else:
                end = end.text

            location = jobs[i].find('span', {"class":"location"})
            if location is None:
                location = ""
            else:
                location = location.text

            jobsDict[i] = {"title": title, "company": company, "industry": industry,
                           "start": start, "end": end, "location": location}

    return {"name": name, "jobs": jobsDict}


def main():

    global _lvl1
    global _lvl2
    global _lvl3

    letterStart = 1
    letterEnd = 2

    all_profiles = []
    nameDirectories = getNames()
    all_data  = {}
    all_titles = []
    for name in nameDirectories[letterStart:letterEnd]:
        all_profiles += getProfiles(name)

    print all_profiles
    print "Scraped " + str(len(all_profiles)) + " Profile URLS"

    for profile in all_profiles:
        all_data[profile] = getPerson(profile)
    for val in all_data.values():
        jobs = val["jobs"]
        for job in jobs.values():
            all_titles.append(job['title'])

    print all_profiles
    print "Scraped " + str(len(all_profiles)) + " Profile URLS"

    print all_data
    print all_titles

    print len(all_data)
    print len(all_titles)

    letters = []
    for name in nameDirectories[letterStart:letterEnd]:
        letters.append(name[-1])
    letters = "".join(letters)

    with open('LinkedInData_%s_%i_%i_%i.json' % (letters, _lvl1, _lvl2, _lvl3), 'wb') as out_file:
        json.dump(all_data, out_file)

main()