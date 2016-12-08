# Band scraper for Roskilde Festival's website 
Scraper for Roskilde Festival webpage (www.roskilde-festival.dk).  Scraping the info about the announced bands a specific year

I have translated the most important thing from danish to english. The rest will come. 
And in some time I will write some documentation at how to use it. 

## Quick-guide for use: 
It will use the current year as default, but the Roskilde Festival has already begun (as of november 2016) to release bands for the upcomming year (2017). 
So it will fail if you just run the script now (in 2016), because Roskilde Festival is already in 2017. 
Therefore the script takes an argument which is the the year, as so:
```bash
./RfBandScraping.py 2017
```

The result of the above (should be) the band names for the upcomming year 2017. 

## Dependencies
- Selenium
- PhantomJS
- tqdm
- dateutil
- MySQLdb (for now)

My ultimative goal is to make an Python install so it will install all dependencies automatically


## Issues and to-do
- Argument to choose to save bands in database or a file
- Arguments for when to save to the database (host, password etc.)
- Autodetect if a year is upcomming or old
- Scraping old years

