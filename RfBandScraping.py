#!/usr/bin/env python3
import sys
from time import sleep
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from collections import defaultdict
import pprint
import MySQLdb
import datetime
from tqdm import tqdm
from dateutil.parser import parse
from chardet.universaldetector import UniversalDetector

from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


class RfBandScraping:

    """docstring for PeopleUpdater"""

    def __init__(self, year):
        print("Selenium webdriver Version: %s" % (webdriver.__version__))
        self.current_year = year
        self.browser = self.init_driver()
        self.bands = defaultdict(dict)
        self.band_list = None
        self.page_info = defaultdict(dict)
        self.page_info[
            'bands_as_list_xpath'] = '//*[@id="ng-app"]/body/div[2]/div[2]/\
                                      div[2]/div[1]/div[2]/div[1]/section/\
                                      div/label[2]'
        self.page_info[
            'bands_as_poster_xpath'] = '//*[@id="ng-app"]/body/div[2]/div[2]\
                                        /div[2]/div[1]/div[2]/div[1]/section/\
                                        div/label[3]'
        self.page_info[
            'poster_headliners_xpath'] = '//*[@id="ng-app"]/body/div[2]/\
                                          div[2]/div[2]/div[1]/div[3]/div/\
                                          div[1]/div[1]'
        self.page_info[
            'poster_bignames_xpath'] = '//*[@id="ng-app"]/body/div[2]/\
                                          div[2]/div[2]/div[1]/div[3]/div/\
                                          div[1]/div[2]'
        self.page_info[
            'poster_common_names_xpath'] = '//*[@id="ng-app"]/body/div[2]/\
                                         div[2]/div[2]/div[1]/div[3]/div/\
                                         div[1]/div[3]'
        self.page_info[
            'poster_small_names_xpath'] = '//*[@id="ng-app"]/body/div[2]/\
                                          div[2]/div[2]/div[1]/div[3]/div/\
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

    def load_page(self):
        self.browser.get(
            "http://www.roskilde-festival.dk/music/" + str(self.current_year))
        self.browser.save_screenshot('start_page.png')
        music_link = None
        try:
            music_link = self.browser.find_element(
                By.XPATH, '//*[@id="ng-app"]/body/div[2]/nav/div[1]/div[2]\
                /ul/li[2]/a')
            music_link.click()
        except:
            print("ohh dammit!")

    def get_music_as_list(self):
        self.browser.get(
            "http://www.roskilde-festival.dk/music/" + str(self.current_year))
        link = None
        try:
            link = self.browser.find_element(
                By.XPATH, self.page_info['bands_as_list_xpath'])
        except Exception:
            print("Couldn't find the link to get the bands as list form")

        try:
            sleep(2)
            link.click()
        except Exception as e:
            print("Couldn't click on the link to the band list: {0}".format(e))
        sleep(3)

        band_list = None
        try:
            band_list = self.browser.find_element(
                By.XPATH, '//*[@id="ng-app"]/body/div[2]/div[2]/div[2]/div[1]/\
                div[3]/div/div[1]/ul')
        except Exception as e:
            print("Could find the list with bands: {0}".format(e))

        script = """var elements = document.getElementsByClassName(\
                    'app__scroller app__scroller--artists ng-scope');
                    var element = elements[0];
                    element.scrollTop = element.scrollHeight;"""

        self.scroll_page_to_bottom(script)
        if band_list is not None:
            try:
                self.band_list = band_list.find_elements(By.TAG_NAME, 'li')
                print("Band li tags found")
            except Exception:
                print("Couldn't find band li tags")
        self.band_list = [elem for i, elem in enumerate(self.band_list)
                          if i % 6 == 0]

    def scroll_page_to_bottom(self, script):
        count = 0
        length = len(self.browser.page_source)
        while True:
            self.browser.execute_script(script)
            print("Scrolling page...")
            sleep(1)
            if length == len(self.browser.page_source):
                if count >= 3:
                    break
                count += 1
            length = len(self.browser.page_source)

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
        for elem in tqdm(self.band_list):
            try:
                link = elem.find_element(By.TAG_NAME, 'header')
                band = None
                try:
                    band = link.find_element(By.TAG_NAME, 'h1')
                    country = link.find_elements(By.TAG_NAME, 'span')[2]
                    self.bands[band.text]['country'] = country.text
                    self.bands[band.text]['link'] = band
                    self.bands[band.text]['category'] = None
                    self.bands[band.text]['category_length'] = None
                    try:
                        play_info_div = link.find_element(
                            By.CSS_SELECTOR, 'div.media__artist-gig')
                        try:
                            spans = play_info_div.find_elements(
                                By.CSS_SELECTOR, 'span')
                            play_info = spans[0].text
                            stage = play_info[play_info.rfind(" ") + 1:]
                            play_info = play_info[:play_info.rfind(" ") - 1]
                            year = play_info[-4:]
                            play_info = play_info[:-6]
                            stage = stage.title()
                            spilletime = (play_info[: -6] + " " + year +
                                          " " + play_info[-5:]).title()
                            self.bands[band.text]['stage'] = stage
                            self.bands[band.text]['time'] = parse(
                                spilletime, fuzzy=True)
                        except Exception:
                            print(
                                "Couldn't find the 'spans' in play_info_div (no info about which stage and time the band will play, is released yet)")
                            self.bands[band.text]['stage'] = None
                            self.bands[band.text]['time'] = None
                    except Exception:
                        print("Couldn't find play_info_div")
                        self.bands[band.text]['stage'] = None
                        self.bands[band.text]['time'] = None
                except Exception as e:
                    print(
                        "Could find the name and/or country of the band: {}".
                        format(str(e)))
            except Exception as e:
                print("Couldn't execute: {0}".format(e))
        print("Number of bands: {}".format(len(self.bands)))
        pprint.pprint(self.bands)

    def get_spilleplan(self):
        pass

    def get_category(self):
        print("get_category")
        self.browser.get(
            "http://www.roskilde-festival.dk/music/" + str(self.current_year))
        sleep(2)
        poster_link = None
        try:
            print("Try to find the link to the poster")
            poster_link = self.browser.find_element(
                By.XPATH, self.page_info['bands_as_poster_xpath'])
            poster_link.click()
        except:
            print("øv")
        print("sover 2 sek")
        sleep(2)
        # self.browser.save_screenshot('poster.png')

        headliners_div = None
        big_names_div = None
        common_names_div = None
        small_names_div = None
        sleep(2)
        print("Fetching divs...")
        try:
            headliners_div = self.browser.find_element(
                By.XPATH, self.page_info['poster_headliners_xpath'])
            big_names_div = self.browser.find_element(
                By.XPATH, self.page_info['poster_bignames_xpath'])
            common_names_div = self.browser.find_element(
                By.XPATH, self.page_info['poster_common_names_xpath'])
            small_names_div = self.browser.find_element(
                By.XPATH, self.page_info['poster_small_names_xpath'])
        except Exception:
            print("Kunne ikke finde placat divs")

        headliners = None
        big_names = None
        common_names = None
        small_names = None
        try:
            headliners = headliners_div.find_elements(By.TAG_NAME, 'li')
            big_names = big_names_div.find_elements(By.TAG_NAME, 'li')
            common_names = common_names_div.find_elements(By.TAG_NAME, 'li')
            small_names = small_names_div.find_elements(By.TAG_NAME, 'li')
        except Exception as e:
            raise

        print("Fetching headliners...")
        for band in tqdm(headliners):
            try:
                band_navn = band.find_element(By.TAG_NAME, 'h1')
                self.bands[band_navn.text]['category'] = self.categories[
                    'headliners']['category']
                self.bands[band_navn.text]['category_length'] = \
                    self.categories['headliners']['playlength']
            except Exception as e:
                print("Kunne ikke finde band navn i headliners")

        print("Fetching big names...")
        for band in tqdm(big_names):
            try:
                band_navn = band.find_element(By.TAG_NAME, 'h2')
                self.bands[band_navn.text]['category'] = self.categories[
                    'big_names']['category']
                self.bands[band_navn.text]['category_length'] = \
                    self.categories['big_names']['playlength']
            except Exception as e:
                print("Couldn't find band name in big_names")

        print("Fetching common names...")
        for band in tqdm(common_names):
            try:
                band_navn = band.find_element(By.TAG_NAME, 'h3')
                self.bands[band_navn.text]['category'] = self.categories[
                    'common_names']['category']
                self.bands[band_navn.text]['category_length'] = \
                    self.categories['common_names']['playlength']
            except Exception as e:
                print("Couldn't find band name in common_names")

        print("Fetching small names....")
        for band in tqdm(small_names):
            try:
                band_navn = band.find_element(By.TAG_NAME, 'h4')
                self.bands[band_navn.text]['category'] = self.categories[
                    'small_names']['category']
                self.bands[band_navn.text]['category_length'] = \
                    self.categories['small_names']['playlength']
            except Exception as e:
                print("Couldn't find band name in small_names")

        pprint.pprint(self.bands)

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
                    hours_between = (tup[1] - lst[i - 2][1]).seconds / 60 / 60
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


class DatabaseHelper(object):

    """docstring for DatabaseHelper"""

    def __init__(self):
        now = datetime.datetime.now()
        self.current_year = now.year
        with open("db_info.txt", 'r') as f:
            login_info = f.readlines()
        login_info_dict = dict(line.strip().split("=")
                               for line in login_info if not line.startswith("#"))
        self.db = MySQLdb.connect(host=login_info_dict["host"],
                                  user=login_info_dict["user"],
                                  passwd=login_info_dict["password"],
                                  db=login_info_dict["db"],
                                  port=login_info_dict["port"],
                                  charset='utf8')
        self.current_bands = self.fetch_current_bands()

    def fetch_current_bands(self):
        cursor = self.db.cursor()
        # print(self.current_year)
        cursor.execute(
            """SELECT * FROM band_spilleplan WHERE aar=%s""",
            (self.current_year,))

        result = defaultdict(dict)
        rows = cursor.fetchall()
        # print(rows)
        for row in rows:
            result[row[1]]['time'] = row[2]
            result[row[1]]['stage'] = row[3]
            result[row[1]]['category'] = row[4]

        return result

    def insert_update_bands(self, bands):
        print("insert_update_bands")
        sql_insert = []
        sql_update = []
        #current_bands = self.fetch_current_bands()
        new_bands = []
        i = 1
        for band, _ in tqdm(bands.items()):
            # print(i)
            cat = bands[band]['category']
            spilletime = bands[band]['time']
            stage = bands[band]['stage']
            if band in self.current_bands:
                #print("{} skal opdateres?".format(band))
                if self.current_bands[band]['category'] != cat:
                    print("categoryen for {} skal opdateres".format(band))
                if self.current_bands[band]['time'] != spilletime:
                    print("spilletime for {} skal opdateres".format(band))
                if self.current_bands[band]['stage'] != spilletime:
                    print("stage for {} skal opdateres".format(band))
            else:
                # .encode('utf-8')
                sql_insert.append(
                    (self.current_year, band, spilletime, stage, cat))
                new_bands.append(band)
            i += 1
        if sql_insert:
            print(
                "Number of new bands: {}\n--------------".format(len(new_bands)))
            # print(new_bands)
            # print(sql_insert)

            cursor = self.db.cursor()
            try:
                cursor.executemany(
                    "INSERT INTO band_spilleplan VALUES(%s, %s, %s, %s, %s);",
                    sql_insert)
                self.db.commit()
            except Exception as e:
                print("Der opstod en fejl: {}".format(str(e)))

    def delete_bands(self, bands):
        pass

    def insert_update_categories(self, categories):
        sql_insert = []
        sql_update = []
        current_categories = self.fetch_current_categories()
        for key, sub_dict in categories.items():
            vals = list(set(sub_dict.keys()))
            if "category" in vals and 'playlength' in vals and 'db_navn' in vals:
                cat = categories[key]['category']
                playlength = categories[key]['playlength']
                db_navn = categories[key]['db_navn']
                if cat in current_categories:
                    print("{} findes allerede. Skal tjekkes".format(cat))
                    if db_navn != current_categories['db_navn'] or \
                            playlength != \
                            current_categories['playlength']:
                        sql_update.append((cat, db_navn, playlength, cat))
                else:
                    sql_insert.append((cat, db_navn, playlength))
                    print("{} mangler!".format(cat))
            print("{} = {} ".format(key, vals))
        #print("sql = {}".format(sql))
        if sql_insert:
            cursor = self.db.cursor()
            cursor.executemany(
                "INSERT INTO band_category VALUES(%s, %s, %s);", sql_insert)
            self.db.commit()
        if sql_update:
            cursor = self.db.cursor()
            cursor.executemany("""UPDATE band_category
                                  SET category=%s, category_tekst=%s, \
                                  koncert_langde=%s
                                  WHERE category=%s;""", sql_update)
            self.db.commit()

    def fetch_current_categories(self):
        cursor = self.db.cursor()
        cursor.execute("""SELECT * FROM band_kategori""")
        result = defaultdict(dict)
        rows = cursor.fetchall()
        for row in rows:
            result[row[0]]['db_navn'] = row[1]
            result[row[0]]['playlength'] = row[2]
        return result


if __name__ == '__main__':
    now = datetime.datetime.now()
    year = now.year
    if len(sys.argv) == 2:
        year = sys.argv[1]
    rfbs = RfBandScraping(year)
    #d = DatabaseHelper()
    # d.insert_update_categories(rfbs.categories)

    rfbs.get_music_as_list()
    rfbs.extract_bands()

    # rfbs.spilletime_leg()
    rfbs.get_category()

    # d.insert_update_bands(rfbs.bands)
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
