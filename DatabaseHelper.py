import pymysql.cursors
from collections import defaultdict
from tqdm import tqdm


class DatabaseHelper:

    """docstring for DatabaseHelper"""

    def __init__(self, year):
        self.current_year = year
        with open("db_info.txt", 'r') as f:
            login_info = f.readlines()
        login_info_dict = dict(line.strip().split("=")
                               for line in login_info if not line.startswith("#"))
        login_info_dict = {k.replace(' ', ''): v.replace(' ', '') for k, v in login_info_dict.items()}
        print(login_info_dict)
        self.db = pymysql.connect(host=login_info_dict["host"],
                                  user=login_info_dict["user"],
                                  passwd=login_info_dict["password"],
                                  db=login_info_dict["db"],
                                  port=int(login_info_dict["port"]),
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
            print(band)
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
        cursor = self.db.cursor()
        try:
            cursor.executemany(
               "DELETE FROM band_spilleplan WHERE band_navn=%s AND aar=%s;",
               list(set(self.current_bands.keys()) - set(bands.keys())),
               self.current_year)
            self.db.commit()
        except Exception as e:
            print("Der opstod en fejl: {}".format(str(e)))


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
                "INSERT INTO band_kategori VALUES(%s, %s, %s);", sql_insert)
            self.db.commit()
        if sql_update:
            cursor = self.db.cursor()
            cursor.executemany("""UPDATE band_kategori
                                  SET kategori=%s, kategori_tekst=%s, \
                                  koncert_laengde=%s
                                  WHERE kategori=%s;""", sql_update)
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
