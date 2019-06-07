#!/usr/bin/env python3
# -*- coding: utf8 -*-  
import sys
# sys.setdefaultencoding('utf8')
from time import sleep
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from collections import defaultdict
import pprint
import datetime
from tqdm import tqdm
from dateutil.parser import parse
#from chardet.universaldetector import UniversalDetector
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from bs4 import BeautifulSoup

from argparse import ArgumentParser
from argparse import RawTextHelpFormatter

from DatabaseHelper import DatabaseHelper

import socket
# import sys
import dateparser

class RfBandScraping:
    root_url = "https://www.roskilde-festival.dk/en/line-up/"

    """docstring for PeopleUpdater"""

    def __init__(self, year=None):
        #print("Selenium webdriver Version: %s" % (webdriver.__version__))
        self.browser = self.init_driver()
        self.current_year = year if year else self.detectYear()
        self.bands = defaultdict(dict)
        self.band_list = None
        self.page_info = defaultdict(dict)
        self.page_info[
            'bands_as_list_xpath'] = '//*[@id="ng-app"]/body/div[2]/div[2]/\
                                      div/div/filter-component/div/div[1]/\
                                      section/div/label[2]'



        #'//*[@id="ng-app"]/body/div[2]/div[2]/\
        # div[2]/div[1]/div[2]/div[1]/section/\
        # div/label[2]'

        self.page_info[
            'bands_as_poster_xpath'] = '//*[@id="ng-app"]/body/div[2]/div[2]\
                                       /div[2]/div/div[1]/div[1]/section/div\
                                       /label[3]'
        self.page_info[
            'poster_headliners_xpath'] = '//*[@id="ng-app"]/body/div[2]/div[2]\
                                          /div[2]/div/div[2]/div/div[1]/div[1]'
        self.page_info[
            'poster_bignames_xpath'] = '//*[@id="ng-app"]/body/div[2]/div[2]/\
                                        div[2]/div/div[2]/div/div[1]/div[2]'
        self.page_info[
            'poster_common_names_xpath'] = '//*[@id="ng-app"]/body/div[2]/\
                                            div[2]/div[2]/div/div[2]/div/\
                                            div[1]/div[3]'
        self.page_info[
            'poster_small_names_xpath'] = '//*[@id="ng-app"]/body/div[2]/\
                                           div[2]/div[2]/div/div[2]/div/\
                                           div[1]/div[4]'
        self.categories = defaultdict(dict)
        self.categories['headliners']['category'] = 1
        self.categories['headliners']['playlength'] = 2.0
        self.categories['headliners']['db_navn'] = "headliners"
        self.categories['big_names']['category'] = 2
        self.categories['big_names']['playlength'] = 1.5
        self.categories['big_names']['db_navn'] = "Stort navn"
        self.categories['common_names']['category'] = 3
        self.categories['common_names']['playlength'] = 1.0
        self.categories['common_names']['db_navn'] = "Almindeligt navn"
        self.categories['small_names']['category'] = 4
        self.categories['small_names']['playlength'] = 1.0
        self.categories['small_names']['db_navn'] = "Lille navn"
        self.cats = ["", "headliners", "big_names", "common_names", "small_names"]

    def init_driver(self):
        dcap = dict(DesiredCapabilities.PHANTOMJS)
        dcap['phantomjs.page.settings.userAgent'] = (
            "User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:45.0) \
            Gecko/20100101 Firefox/45.0")
        driver = webdriver.PhantomJS(desired_capabilities=dcap, service_args=[
                                     '--ignore-ssl-errors=true',
                                     '--ssl-protocol=any',
                                     '--web-security=false'])
        driver.set_window_size(1920, 1080)
        # black backgound on screenshot
        driver.execute_script('document.body.style.background = "white"')
        return driver

    def scroll_page_to_bottom(self, script):
        count = 0
        length = len(self.browser.page_source)
        while True:
            self.browser.execute_script(script)
            print("Scrolling page...")
            sleep(.5)
            if length == len(self.browser.page_source):
                if count >= 3:
                    break
                count += 1
            length = len(self.browser.page_source)

    def extract_bands2(self):
        kategori_status = self.get_category()
        print(kategori_status)
        self.browser.get(
            self.root_url + str(self.current_year))

        script = """document.querySelector(".filter label:nth-of-type(2)").click();
                    var elements = document.getElementsByClassName(\
                    'app__scroller app__scroller--artists ng-scope');
                    var element = elements[0];
                    element.scrollTop = element.scrollHeight;"""

        self.scroll_page_to_bottom(script)
        soup = BeautifulSoup(self.browser.page_source, 'html.parser')
        # bands = soup.select(".feature__content.media")
        bands = soup.select("li.media-list__item")
        # spil_plan = soup.select(".feature__artist-gig")
        for i, band in enumerate(bands):
            band_name = band.find("span", {"data-ng-bind": "artist.displayName"}).text.upper()
            country = band.find("span", {"data-ng-bind": "countryList"})
            time = band.select("span:nth-of-type(5)")
            if(len(time) > 0):
                time = dateparser.parse(str(time[0]).split("YYYY'\">")[1].split(",</span>")[0])
            else:
                time = None
            stage = band.select("span:nth-of-type(6)")
            print(stage)
            if(len(stage) > 0):
                stage = str(stage[0]).split("\">")[1].split("</span>")[0]
            else:
                stage = None
            self.bands[band_name]['country'] = country.text.upper()
            #self.bands[band_name]['link'] = band
            if not kategori_status: #hvis plakaten ikke er udgivet endnu
                self.bands[band_name]['category'] = self.categories['common_names']['category']
                self.bands[band_name]['category_length'] = self.categories['common_names']['playlength']
            self.bands[band_name]['stage'] = stage
            self.bands[band_name]['time'] = time
            #band_spilleplan = spil_plan[i]
            # blah, blah

    def extract_bands(self):
        """
        Fetching bands (navne og deres land) og gemmer i et dict. 
        Band-navnet er key og derefter har den 4 yderligere keys:
        - 'country'  - bandets land (String)
        - 'link'     - link til bandets underside, til at kunne finde spillested/stage og spilletime (selenium webelement)
        - 'stage'    - stagen hvor bandet spiller (String - default: '')
        - 'time'      - Hvornår bandet spiller (dag og time) (String - default: '')

        """
        print("extract_bands")
        sleep(5)
        play_info_faults = []
        for elem in tqdm(self.band_list):
            try:
                link = elem.find_element(By.TAG_NAME, 'header')
                band = None
                try:
                    band = link.find_element(By.TAG_NAME, 'h1')
                    # .encode('utf-8')#  .decode('utf-8')
                    band_name = band.text
                    # if isinstance(band_name, str):
                    #     print("ja!")
                    #     band_name = unicode(band_name, "utf-8")
                    # print(type(band_name))
                    country = link.find_elements(By.TAG_NAME, 'span')[2]
                    self.bands[band_name]['country'] = country.text
                    self.bands[band_name]['link'] = band
                    self.bands[band_name]['category'] = None
                    self.bands[band_name]['category_length'] = None
                    try:
                        play_info_div = link.find_element(
                            By.CSS_SELECTOR, 'div.media__artist-gig')
                        try:
                            spans = play_info_div.find_elements(
                                By.CSS_SELECTOR, 'article > header > div > div > span')  # 'span'
                            play_info = spans[0].text
                            stage = play_info[play_info.rfind(" ") + 1:]
                            play_info = play_info[:play_info.rfind(" ") - 1]
                            year = play_info[-4:]
                            play_info = play_info[:-6]
                            stage = stage.title()
                            spilletime = (play_info[: -6] + " " + year +
                                          " " + play_info[-5:]).title()
                            self.bands[band_name]['stage'] = stage
                            self.bands[band_name]['time'] = parse(
                                spilletime, fuzzy=True)
                        except Exception:
                            play_info_faults.append(band_name)
                            self.bands[band_name]['stage'] = None
                            self.bands[band_name]['time'] = None
                    except Exception:
                        print("Couldn't find play_info_div")
                        self.bands[band_name]['stage'] = None
                        self.bands[band_name]['time'] = None
                except Exception as e:
                    print(
                        "Could find the name and/or country of the band: {}".
                        format(str(e)))
            except Exception as e:
                print("Couldn't execute: {0}".format(e))
        # pprint.pprint(self.bands)
        #print("Number of bands: {}".format(len(self.bands)))
        if play_info_faults:
            # Couldn't find the 'spans' in play_info_div
            print("Couldn't find info about which stage and time the band will play for theese bands:\n{}"
                  .format(play_info_faults, len(self.bands)))
        # self.bands.pop("NONAME")
        # self.bands.pop("NEUROSIS")
        # pprint.pprint(self.bands)
        # sys.exit()

    def detectYear(self):
        """ Get the working year at Roskilde Festival

        Getting the working year at Roskilde Festival,
        by extracting the year from the logo

        Returns:
            integer -- The working year
        """
        self.browser.get("http://www.roskilde-festival.dk")
        soup = BeautifulSoup(self.browser.page_source, 'html.parser')
        return soup.find("figure", class_="logo").text.strip()

    def get_spilleplan(self):
        pass

    def get_category(self):
        print("get_category")
        self.browser.get(
            self.root_url + str(self.current_year))

        script = """document.querySelector(".filter label:nth-of-type(3)").click();
                    var elements = document.getElementsByClassName(\
                    'app__scroller app__scroller--artists ng-scope');
                    var element = elements[0];
                    element.scrollTop = element.scrollHeight;"""

        self.scroll_page_to_bottom(script)
        soup = BeautifulSoup(self.browser.page_source, 'html.parser')
        bands = soup.select("div.poster-list")
        # print(bands)

        listen = str(bands).split("<span>poster</span>")[1].split("<!-- end ngIf: artist.showInBandList --><!-- end ngRepeat: artist in value | orderBy:'sortingName' --><!-- ngIf: artist.showInBandList -->")
        print("Found {} bands on the poster".format(len(listen)))
        for band in listen:
            tmp = str(band)
            name = tmp.split('data-ng-bind="artist.displayName">')[1].split("</em>")[0]
            category = tmp.split('class="priority-')[1].split("\" data-ng-if=")[0]
            self.bands[name]['category'] = category
            self.bands[name]['category_length'] = self.categories[self.cats[int(category)]]['playlength']
        return True

        #print("Fetching headliners...")
        for band in tqdm(headliners):
            try:
                band_name = band.find_element(
                    By.TAG_NAME, 'h1').find_element(By.TAG_NAME, 'em')
                self.bands[band_name.text]['category'] = self.categories[
                    'headliners']['category']
                self.bands[band_name.text]['category_length'] = \
                    self.categories['headliners']['playlength']
            except Exception as e:
                print("Couldn't find {} in headliners".format(band))

        #print("Fetching big names...")
        for band in tqdm(big_names):
            try:
                band_name = band.find_element(
                    By.TAG_NAME, 'h2').find_element(By.TAG_NAME, 'em')
                self.bands[band_name.text]['category'] = self.categories[
                    'big_names']['category']
                self.bands[band_name.text]['category_length'] = \
                    self.categories['big_names']['playlength']
            except Exception as e:
                print("Couldn't find {} in big_names".format(band))

        #print("Fetching common names...")
        for band in tqdm(common_names):
            try:
                band_name = band.find_element(
                    By.TAG_NAME, 'h3').find_element(By.TAG_NAME, 'em')
                self.bands[band_name.text]['category'] = self.categories[
                    'common_names']['category']
                self.bands[band_name.text]['category_length'] = \
                    self.categories['common_names']['playlength']
            except Exception as e:
                print("Couldn't find {} in common_names".format(band))

        #print("Fetching small names....")
        for band in tqdm(small_names):
            try:
                band_name = band.find_element(
                    By.TAG_NAME, 'h4').find_element(By.TAG_NAME, 'em')
                self.bands[band_name.text]['category'] = self.categories[
                    'small_names']['category']
                self.bands[band_name.text]['category_length'] = \
                    self.categories['small_names']['playlength']
            except Exception as e:
                print("Couldn't find {} in small_names".format(band))

        return True
        # self.bands.pop("NONAME")
        # self.bands.pop("NEUROSIS")

        # pprint.pprint(self.bands)
        #print("Number of bands: {}".format(len(self.bands)))

    """
    An experimentel methods
    """

    def spilletime_leg(self):
        d = defaultdict(list)
        dd = defaultdict(dict)
        lst = []
        for band, _ in tqdm(self.bands.items()):
            d[self.bands[band]['stage']].append(
                (band, self.bands[band]['time'], 0.0))

        for stage, lst in tqdm(d.items()):
            d[stage] = sorted(lst, key=lambda x: x[1])

        for stage, lst in d.items():
            temp_dag = '-1'
            if stage == "Street":
                print(lst)
            for i, tup in enumerate(lst, start=1):
                if i < len(lst):
                    hours_between = (lst[i][1] - tup[1]).seconds / 60 / 60
                    if stage == "Street":
                        print(hours_between)
                    if hours_between < 6.0:
                        if int(temp_dag) == -1:
                            temp_dag = tup[1].strftime("%w")
                        if temp_dag not in dd[stage]:
                            dd[stage][temp_dag] = [tup]
                        else:
                            dd[stage][temp_dag].append(tup)
                    else:
                        if hours_between < 16.0:
                            if str(temp_dag) != '-1':
                                dd[stage][temp_dag].append(tup)
                            else:
                                print("feeejl???")
                            temp_dag = str(int(temp_dag) + 1)
                            print("stage = {} - band = {}\n    time = {}\n----------\n".
                                  format(stage, tup[0], tup[1]))
                            # print("i = {} - stage = {} - band = {}\n    time = {}\n    hb = {}\n----------\n".
                            # format(i, stage, lst[i][0], lst[i][1],
                            # hours_between))
                        else:
                            temp_dag = str(int(temp_dag) + 1)
                            dd[stage][temp_dag] = [tup]
                else:
                    # if len(lst) == 1:
                    if tup[1] is not None and lst[i - 2][1] is not None:
                        hours_between = (
                            tup[1] - lst[i - 2][1]).seconds / 60 / 60
                        if hours_between < 6.0:
                            if int(temp_dag) == -1:
                                temp_dag = tup[1].strftime("%w")
                            if temp_dag not in dd[stage]:
                                dd[stage][temp_dag] = [tup]
                            else:
                                dd[stage][temp_dag].append(tup)
                        else:
                            if hours_between < 16.0:
                                if str(temp_dag) != '-1':
                                    dd[stage][temp_dag].append(tup)
                                else:
                                    print("feeejl???")
                                temp_dag = str(int(temp_dag) + 1)
                                print("stage = {} - band = {}\n    time = {}\n----------\n".
                                      format(stage, tup[0], tup[1]))
                                # print("i = {} - stage = {} - band = {}\n    time = {}\n    hb = {}\n----------\n".
                                # format(i, stage, lst[i][0], lst[i][1],
                                # hours_between))
                            else:
                                temp_dag = str(int(temp_dag) + 1)
                                dd[stage][temp_dag].append(tup)

        #[('BABY BLOOD', datetime.datetime(2016, 6, 26, 20, 0), 0.0),
        # ('M.I.L.K.',   datetime.datetime(2016, 6, 27, 20, 0), 0.0),
        # ('KHALAZER',   datetime.datetime(2016, 6, 28, 20, 0), 0.0)]
        #
        # print("\n\n\n\n----------------\n\n\n")
        pprint.pprint(dd)
        # print(dd['Orange'][3])
        for stage, dag_key in dd.items():
            for dag, lst in dag_key.items():
                s = 0.0
                for i, tup in enumerate(lst, start=1):
                    band, time, _ = tup
                    if i < len(lst):
                        time2 = lst[i][1]
                        # 30 til stage-skift
                        dur_minutes = ((time2 - time).seconds / 60) - 30
                        s += dur_minutes
                        d[stage] = self.updates_time_in_tuple(
                            dur_minutes, band, d[stage])
                    else:
                        mean = s / len(lst)
                        d[stage] = self.updates_time_in_tuple(
                            mean, band, d[stage])

        pprint.pprint(d)

    def updates_time_in_tuple(self, value, band, lst_of_tuples):
        return [(b, t, d) if b != band else (b, t, value) for (b, t, d) in lst_of_tuples]

    def get_categories(self):
        return self.categories

    def get_bands(self):
        return self.bands

    def get_year(self):
        return self.current_year

"""
domain socket: avoid script to run if it already running
"""


def get_lock(process_name):
    # Without holding a reference to our socket somewhere it gets garbage
    # collected when the function exits
    get_lock._lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

    try:
        get_lock._lock_socket.bind('\0' + process_name)
        print('I got the lock')
    except socket.error:
        print('lock exists')
        sys.exit(1)


if __name__ == '__main__':
    get_lock("roskilde_scraper")
    now = datetime.datetime.now()
    year = None  # now.year
    if len(sys.argv) == 2:
        year = sys.argv[1]

    dbinfo_help_text = """Used only with -o="database"\n
File with database and login-informations:
Login-informations as following on a seperate line:
username=[username-value]
port=[port], ect.\n
Database-information:
On each line:
database=[database_name]
table=[table_name] - followed by:
col=[column_name]-->[mapped_key]\n
mapped_key could be band_name. For example:
col=name-->band_name\n
Possible mapped_keys:
band_name, stage, concert_start_time, category, concert_length\n
There can be multiple instance of table and col.
cols must be grouped under the correct table"""
    arg_parser = ArgumentParser(description='Bla bla bla',
                                formatter_class=RawTextHelpFormatter)
    arg_parser.add_argument("-y", "--year", dest="year", metavar="INTEGER",
                            help="Scrape specific year")
    arg_parser.add_argument("-o", "--output", dest="output",
                            choices=["file", "stdout", "database"],
                            help="Choose how to output the scraped data")
    arg_parser.add_argument("-dbinfo", "--database_info", metavar="FILE",
                            dest="dbinfo", help=dbinfo_help_text)

    args = arg_parser.parse_args()
    if args.output == "database" and args.dbinfo is None:
        arg_parser.error("Missing database information file")
    print("############### Roskilde band scraper - log {} ##############".
          format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    rfbs = RfBandScraping(year)
    d = DatabaseHelper(rfbs.current_year)
    # d.insert_update_categories(rfbs.categories)

    #rfbs.get_music_as_list()
    rfbs.extract_bands2()
    # rfbs.spilletime_leg()
    # sys.exit()

    # rfbs.spilletime_leg()
    #rfbs.get_category()
    print("-------------------- Result: ---------------------------")
    pprint.pprint(rfbs.bands)
    d.insert_update_bands(rfbs.bands)
    d.cancel_bands(rfbs.bands)
    print("--------------------------------------------------------\n\n")
    #res = d.fetch_current_bands()
    # pprint.pprint(res)
    # pprint.pprint(rfbs.bands)

"""
TODO:
-------
get_category fejler i vagrant (tilsyneladende)
Derfor:
- Lav en funktion der tilføjer en random category mellem 1 og 4
- udkommenter kaldet til get_category
- kør i vagrant og se om det virker

[description]
"""
