# Band scraper for Roskilde Festival's website 
Scraper for Roskilde Festival webpage (www.roskilde-festival.dk).  Scraping the info about the announced bands a specific year

I have translated the most important thing from danish to english. The rest will come. 
And in some time I will write some documentation at how to use it. 

## Installation
1. Clone/download the files from the repository
2. Download and install PhantomJS version **2.1.1** (or higher) by following [this guide](phantomjs_guide.md).
3. Install Pipy packages: `pip3 install -r requirements.txt`
4. Done! :)


## Quick-guide for use: 
It will find and use the year that Roskilde Festival current uses. 
As in december 2016, it will use 2017 as the current year:
```bash
./RfBandScraping.py
```
The result of the above (should be) the band names for the upcomming year 2017.

If you want to scrape old years, you have to give the year explicit, like this:
```bash
./RfBandScraping.py 2016
```
**OBS: Scraping old years, isn't yet implemented!**

## Dependencies
### Pipy packages 
- Selenium
- BeautifulSoup4
- tqdm
- dateutil
- PyMySQL

### Other tools/dependencies
- PhantomJS>=2.1.1


## Issues and to-do
- Argument to choose to save bands in database or a file
- Arguments for when to save to the database (host, password etc.)
- Scraping old years

