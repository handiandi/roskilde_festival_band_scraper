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
            'poster_hovednavne_xpath'] = '//*[@id="ng-app"]/body/div[2]/\
                                          div[2]/div[2]/div[1]/div[3]/div/\
                                          div[1]/div[1]'
        self.page_info[
            'poster_storenavne_xpath'] = '//*[@id="ng-app"]/body/div[2]/\
                                          div[2]/div[2]/div[1]/div[3]/div/\
                                          div[1]/div[2]'
        self.page_info[
            'poster_alm_navne_xpath'] = '//*[@id="ng-app"]/body/div[2]/\
                                         div[2]/div[2]/div[1]/div[3]/div/\
                                         div[1]/div[3]'
        self.page_info[
            'poster_smaa_navne_xpath'] = '//*[@id="ng-app"]/body/div[2]/\
                                          div[2]/div[2]/div[1]/div[3]/div/\
                                          div[1]/div[4]'
        self.kategorier = defaultdict(dict)
        self.kategorier['hovednavne']['kategori'] = 1
        self.kategorier['hovednavne']['spillelaengde'] = 2.0
        self.kategorier['hovednavne']['db_navn'] = "Hovednavn"
        self.kategorier['store_navne']['kategori'] = 2
        self.kategorier['store_navne']['spillelaengde'] = 1.5
        self.kategorier['store_navne']['db_navn'] = "Stort navn"
        self.kategorier['alm_navne']['kategori'] = 3
        self.kategorier['alm_navne']['spillelaengde'] = 1.0
        self.kategorier['alm_navne']['db_navn'] = "Almindeligt navn"
        self.kategorier['smaa_navne']['kategori'] = 4
        self.kategorier['smaa_navne']['spillelaengde'] = 1.0
        self.kategorier['smaa_navne']['db_navn'] = "Lille navn"

    def init_driver(self):
        dcap = dict(DesiredCapabilities.PHANTOMJS)
        # ("Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36")
        dcap['phantomjs.page.settings.userAgent'] = (
            "User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:45.0) \
            Gecko/20100101 Firefox/45.0")
        #("User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:44.0) Gecko/20100101 Firefox/44.0")
        # service_args=['--ignore-ssl-errors=true', '--ssl-protocol=any',
        # '--web-security=false'])
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
            "http://www.roskilde-festival.dk/music/"+str(self.current_year))
        self.browser.save_screenshot('start_page.png')
        music_link = None
        try:
            music_link = self.browser.find_element(
                By.XPATH, '//*[@id="ng-app"]/body/div[2]/nav/div[1]/div[2]\
                /ul/li[2]/a')
            music_link.click()
        except:
            print("øv")
        if music_link is not None:
            print("Yeah?")
        else:
            print(":(")
        self.browser.save_screenshot('login_foer.png')

    def get_music_as_list(self):
        self.browser.get(
            "http://www.roskilde-festival.dk/music/"+str(self.current_year))
        self.browser.save_screenshot('start_page.png')
        link = None
        try:
            link = self.browser.find_element(
                By.XPATH, self.page_info['bands_as_list_xpath'])
        except Exception:
            print("Kunne ikke finde link til at få bands som liste")

        try:
            self.browser.save_screenshot("foer_get_music_as_list_as_liste.png")
            sleep(2)
            link.click()
        except Exception as e:
            print("Kunne ikke klikke linket til vores liste: {0}".format(e))
        sleep(3)
        self.browser.save_screenshot("efter_get_music_as_list_as_liste.png")

        with open('band_list_source.txt', 'w') as f:
            f.write(self.browser.page_source)
        band_list = None
        try:
            band_list = self.browser.find_element(
                By.XPATH, '//*[@id="ng-app"]/body/div[2]/div[2]/div[2]/div[1]/\
                div[3]/div/div[1]/ul')
        except Exception as e:
            print("Kunne ikke finde listen med bands: {0}".format(e))

        script = """var elements = document.getElementsByClassName(\
                    'app__scroller app__scroller--artists ng-scope');
                    var element = elements[0];
                    element.scrollTop = element.scrollHeight;"""

        self.scroll_page_to_bottom(script)
        if band_list is not None:
            try:
                self.band_list = band_list.find_elements(By.TAG_NAME, 'li')
                print("Band li tags fundet")
            except Exception:
                print("Kunne ikke band li tags")
        self.band_list = [elem for i, elem in enumerate(self.band_list)
                          if i % 6 == 0]
        #print(self.band_list)

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
        Henter bands (navne og deres land) og gemmer i et dict. 
        Band-navnet er key og derefter har den 4 yderligere keys:
        - 'country'  - bandets land (String)
        - 'link'     - link til bandets underside, til at kunne finde spillested/scene og spilletid (selenium webelement)
        - 'scene'    - scenen hvor bandet spiller (String - default: '')
        - 'tid'      - Hvornår bandet spiller (dag og tid) (String - default: '')

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
                    self.bands[band.text]['kategori'] = None
                    self.bands[band.text]['kategori_laengde'] = None
                    try:
                        spille_info_div = link.find_element(
                            By.CSS_SELECTOR, 'div.media__artist-gig')
                        try:
                            spans = spille_info_div.find_elements(
                                By.CSS_SELECTOR, 'span')
                            spille_info = spans[0].text
                            scene = spille_info[spille_info.rfind(" ")+1:]
                            spille_info = spille_info[
                                                    :spille_info.rfind(" ")-1]
                            aar = spille_info[-4:]
                            spille_info = spille_info[:-6]
                            scene = scene.title()
                            spilletid = (spille_info[: -6] + " " + aar +
                                         " " + spille_info[-5:]).title()
                            self.bands[band.text]['scene'] = scene
                            self.bands[band.text]['tid'] = parse(spilletid, fuzzy=True)
                        except Exception:
                            print("Kunne ikke finde spans i spille_info_div")
                            self.bands[band.text]['scene'] = None
                            self.bands[band.text]['tid'] = None
                    except Exception:
                        print("Kunne ikke finde spille_info_div")
                        self.bands[band.text]['scene'] = None
                        self.bands[band.text]['tid'] = None
                except Exception as e:
                    print(
                        "Kunne ikke finde band navn og/eller land: {}".
                        format(str(e)))
            except Exception as e:
                print("Kunne ikke udføre det: {0}".format(e))
        print("Antal bands: {}".format(len(self.bands)))
        pprint.pprint(self.bands)

    def get_spilleplan(self):
        pass

    def get_kategori(self):
        print("get_kategori")
        self.browser.get(
            "http://www.roskilde-festival.dk/music/"+str(self.current_year))
        sleep(2)
        poster_link = None
        try:
            print("prøver at finde link til poster")
            poster_link = self.browser.find_element(
                By.XPATH, self.page_info['bands_as_poster_xpath'])
            poster_link.click()
        except:
            print("øv")
        print("sover 2 sek")
        sleep(2)
        # self.browser.save_screenshot('poster.png')

        hovednavne_div = None
        store_navne_div = None
        alm_navne_div = None
        smaa_navne_div = None
        print("sover 2 sek før henter divs")
        sleep(2)
        print("henter divs...")
        try:
            hovednavne_div = self.browser.find_element(
                By.XPATH, self.page_info['poster_hovednavne_xpath'])
            store_navne_div = self.browser.find_element(
                By.XPATH, self.page_info['poster_storenavne_xpath'])
            alm_navne_div = self.browser.find_element(
                By.XPATH, self.page_info['poster_alm_navne_xpath'])
            smaa_navne_div = self.browser.find_element(
                By.XPATH, self.page_info['poster_smaa_navne_xpath'])
        except Exception:
            print("Kunne ikke finde plakat divs")

        hovednavne = None
        store_navne = None
        alm_navne = None
        smaa_navne = None
        try:
            hovednavne = hovednavne_div.find_elements(By.TAG_NAME, 'li')
            store_navne = store_navne_div.find_elements(By.TAG_NAME, 'li')
            alm_navne = alm_navne_div.find_elements(By.TAG_NAME, 'li')
            smaa_navne = smaa_navne_div.find_elements(By.TAG_NAME, 'li')
        except Exception as e:
            raise

        print("Henter hovednavne...")
        for band in tqdm(hovednavne):
            try:
                band_navn = band.find_element(By.TAG_NAME, 'h1')
                self.bands[band_navn.text]['kategori'] = self.kategorier[
                    'hovednavne']['kategori']
                self.bands[band_navn.text]['kategori_laengde'] = \
                    self.kategorier['hovednavne']['spillelaengde']
            except Exception as e:
                print("Kunne ikke finde band navn i hovednavne")

        print("Henter store navne...")
        for band in tqdm(store_navne):
            try:
                band_navn = band.find_element(By.TAG_NAME, 'h2')
                self.bands[band_navn.text]['kategori'] = self.kategorier[
                    'store_navne']['kategori']
                self.bands[band_navn.text]['kategori_laengde'] = \
                    self.kategorier['store_navne']['spillelaengde']
            except Exception as e:
                print("Kunne ikke finde band navn i store_navne")

        print("Henter alm. navne...")
        for band in tqdm(alm_navne):
            try:
                band_navn = band.find_element(By.TAG_NAME, 'h3')
                self.bands[band_navn.text]['kategori'] = self.kategorier[
                    'alm_navne']['kategori']
                self.bands[band_navn.text]['kategori_laengde'] = \
                    self.kategorier['alm_navne']['spillelaengde']
            except Exception as e:
                print("Kunne ikke finde band navn i alm_navne")

        print("Henter små navne....")
        for band in tqdm(smaa_navne):
            try:
                band_navn = band.find_element(By.TAG_NAME, 'h4')
                self.bands[band_navn.text]['kategori'] = self.kategorier[
                    'smaa_navne']['kategori']
                self.bands[band_navn.text]['kategori_laengde'] = \
                    self.kategorier['smaa_navne']['spillelaengde']
            except Exception as e:
                print("Kunne ikke finde band navn i smaa_navne")

        pprint.pprint(self.bands)

    def spilletid_leg(self):
        d = defaultdict(list)
        dd = defaultdict(dict)
        lst = []
        for band, _ in tqdm(self.bands.items()):
            d[self.bands[band]['scene']].append(
                (band, self.bands[band]['tid'], 0.0))

        for scene, lst in tqdm(d.items()):
            d[scene] = sorted(lst, key=lambda x: x[1])

        for scene, lst in d.items():
            temp_dag = '-1'
            if scene == "Street":
                print(lst)
            for i, tup in enumerate(lst, start=1):
                if i < len(lst):
                    hours_between = (lst[i][1]-tup[1]).seconds/60/60
                    if scene == "Street":
                        print(hours_between)
                    if hours_between < 6.0:
                        if int(temp_dag) == -1:
                            temp_dag = tup[1].strftime("%w")
                        if temp_dag not in dd[scene]:
                            dd[scene][temp_dag] = [tup]
                        else:
                            dd[scene][temp_dag].append(tup)
                    else:
                        if hours_between < 16.0:
                            if str(temp_dag) != '-1':
                                dd[scene][temp_dag].append(tup)
                            else:
                                print("feeejl???")
                            temp_dag = str(int(temp_dag) + 1)
                            print("scene = {} - band = {}\n    tid = {}\n----------\n".
                                  format(scene, tup[0], tup[1]))
                            #print("i = {} - scene = {} - band = {}\n    tid = {}\n    hb = {}\n----------\n".
                            #      format(i, scene, lst[i][0], lst[i][1], hours_between))
                        else:
                            temp_dag = str(int(temp_dag) + 1)
                            dd[scene][temp_dag] = [tup]
                else:
                    #if len(lst) == 1:
                    hours_between = (tup[1]-lst[i-2][1]).seconds/60/60
                    if hours_between < 6.0:
                        if int(temp_dag) == -1:
                            temp_dag = tup[1].strftime("%w")
                        if temp_dag not in dd[scene]:
                            dd[scene][temp_dag] = [tup]
                        else:
                            dd[scene][temp_dag].append(tup)
                    else:
                        if hours_between < 16.0:
                            if str(temp_dag) != '-1':
                                dd[scene][temp_dag].append(tup)
                            else:
                                print("feeejl???")
                            temp_dag = str(int(temp_dag) + 1)
                            print("scene = {} - band = {}\n    tid = {}\n----------\n".
                                  format(scene, tup[0], tup[1]))
                            #print("i = {} - scene = {} - band = {}\n    tid = {}\n    hb = {}\n----------\n".
                            #      format(i, scene, lst[i][0], lst[i][1], hours_between))
                        else:
                            temp_dag = str(int(temp_dag) + 1)
                            dd[scene][temp_dag].append(tup)

        #[('BABY BLOOD', datetime.datetime(2016, 6, 26, 20, 0), 0.0), 
        # ('M.I.L.K.',   datetime.datetime(2016, 6, 27, 20, 0), 0.0), 
        # ('KHALAZER',   datetime.datetime(2016, 6, 28, 20, 0), 0.0)]
        #
        #print("\n\n\n\n----------------\n\n\n")
        pprint.pprint(dd)
        #print(dd['Orange'][3])
        for scene, dag_key in dd.items():
            for dag, lst in dag_key.items():
                s = 0.0
                for i, tup in enumerate(lst, start=1):
                    band, tid, _ = tup
                    if i < len(lst):
                        tid2 = lst[i][1]
                        dur_minutes = ((tid2-tid).seconds/60)-30 #30 til scene-skift
                        s += dur_minutes
                        d[scene] = self.updates_time_in_tuple(dur_minutes, band, d[scene])
                    else:
                        mean = s/len(lst)
                        d[scene] = self.updates_time_in_tuple(mean, band, d[scene])

        pprint.pprint(d)


    def updates_time_in_tuple(self, value, band, lst_of_tuples):
        return [(b, t, d) if b != band else (b, t, value) for (b, t, d) in lst_of_tuples]


    def get_kategorier(self):
        return self.kategorier

    def get_bands(self):
        return self.bands


class DatabaseHelper(object):

    """docstring for DatabaseHelper"""

    def __init__(self):
        now = datetime.datetime.now()
        self.current_year = now.year
        with open("db_info.txt", 'r') af f:
            login_info = f.readlines()
        login_info_dict = dict(line.strip().split("=") for line in login_info if not line.startswith("#"))
        self.db = MySQLdb.connect(host=login_info_dict["host"], user=login_info_dict["user"],
                                  passwd=login_info_dict["password"], db=login_info_dict["db"], port=login_info_dict["port"],
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
            result[row[1]]['tid'] = row[2]
            result[row[1]]['scene'] = row[3]
            result[row[1]]['kategori'] = row[4]

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
            kat = bands[band]['kategori']
            spilletid = bands[band]['tid']
            scene = bands[band]['scene']
            if band in self.current_bands:
                #print("{} skal opdateres?".format(band))
                if self.current_bands[band]['kategori'] != kat:
                    print("kategorien for {} skal opdateres".format(band))
                if self.current_bands[band]['tid'] != spilletid:
                    print("spilletid for {} skal opdateres".format(band))
                if self.current_bands[band]['scene'] != spilletid:
                    print("scene for {} skal opdateres".format(band))
            else:
                # .encode('utf-8')
                sql_insert.append(
                    (self.current_year, band, spilletid, scene, kat))
                new_bands.append(band)
            i += 1
        if sql_insert:
            print("Antal nye bands: {}\n--------------".format(len(new_bands)))
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

    def insert_update_kategorier(self, kategorier):
        sql_insert = []
        sql_update = []
        current_kategorier = self.fetch_current_kategorier()
        for key, sub_dict in kategorier.items():
            vals = list(set(sub_dict.keys()))
            if "kategori" in vals and 'spillelaengde' in vals and 'db_navn' in vals:
                kat = kategorier[key]['kategori']
                spillelaengde = kategorier[key]['spillelaengde']
                db_navn = kategorier[key]['db_navn']
                if kat in current_kategorier:
                    print("{} findes allerede. Skal tjekkes".format(kat))
                    if db_navn != current_kategorier['db_navn'] or \
                            spillelaengde != \
                            current_kategorier['spillelaengde']:
                        sql_update.append((kat, db_navn, spillelaengde, kat))
                else:
                    sql_insert.append((kat, db_navn, spillelaengde))
                    print("{} mangler!".format(kat))
            print("{} = {} ".format(key, vals))
        #print("sql = {}".format(sql))
        if sql_insert:
            cursor = self.db.cursor()
            cursor.executemany(
                "INSERT INTO band_kategori VALUES(%s, %s, %s);", sql_insert)
            self.db.commit()
        if sql_update:
            cursor = self.db.cursor()
            cursor.executemany("""UPDATE band_kategori
                                  SET kategori=%s, kategori_tekst=%s, \
                                  koncert_langde=%s
                                  WHERE kategori=%s;""", sql_update)
            self.db.commit()

    def fetch_current_kategorier(self):
        cursor = self.db.cursor()
        cursor.execute("""SELECT * FROM band_kategori""")
        result = defaultdict(dict)
        rows = cursor.fetchall()
        for row in rows:
            result[row[0]]['db_navn'] = row[1]
            result[row[0]]['spillelaengde'] = row[2]
        return result


if __name__ == '__main__':
    now = datetime.datetime.now()
    year = now.year
    print("Antal argumenter = {0}".format(len(sys.argv)))
    if len(sys.argv) ==  2:
        year = sys.argv[1]
    rfbs = RfBandScraping(year)
    #d = DatabaseHelper()
    #d.insert_update_kategorier(rfbs.kategorier)
    
    rfbs.get_music_as_list()
    rfbs.extract_bands()
    
    #rfbs.spilletid_leg()
    rfbs.get_kategori()


    #d.insert_update_bands(rfbs.bands)
    #res = d.fetch_current_bands()
    #pprint.pprint(res)
    #pprint.pprint(rfbs.bands)

"""
TODO:
-------
get_kategori fejler i vagrant (tilsyneladende)
Derfor:
- Lav en funktion der tilføjer en random kategori mellem 1 og 4
- udkommenter kaldet til get_kategori
- kør i vagrant og se om det virker

[description]
"""
