import scrapy
import sqlite3
import urllib.parse as ul
from bs4 import BeautifulSoup

db_name = '../im.db'


class Series(scrapy.Item):
    name = scrapy.Field()
    code = scrapy.Field()


class ImdbSpider(scrapy.Spider):
    name = "imdb"
    urls = []

    def __init__(self):
        global db_name
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        s_table = ''' CREATE TABLE IF NOT EXISTS tv_series (series text,
                                                            season integer,
                                                            episode integer,
                                                            name text) '''
        c.execute(s_table)
        conn.commit()

        # query = input('Enter movie/tv series:\n')
        # query = query.replace(' ', '+')

        # testing
        url = 'http://www.imdb.com/find?ref_=nv_sr_fn&q=parks+and+recreation&s=all'
        self.urls.append(url)
        # if url.split(':')[0] in ['http', 'https']:
        #     self.urls.append(url)
        # else:
        #     url = 'http://%s' % url
        #     self.urls.append(url)

    def start_requests(self):
        for url in self.urls:
            yield scrapy.Request(url=url, callback=self.parse_search)

    def parse_search(self, response):
        series = Series()

        search_res = response.css('tr.findResult')
        name = search_res.css('td.result_text').css('a::text').extract_first()
        suffix = search_res.css('a::attr(href)').extract_first()

        url = 'http://www.imdb.com%s' % suffix
        series['name'] = name
        # title code is the part before '?' /title/tt1266020/?ref_=fn_al_tt_1
        series['code'] = suffix.split('?')[0]

        # IF movie: parse_movie
        # IF series: parse_series
        request = scrapy.Request(url=url, callback=self.parse_series)
        request.meta['series'] = series
        yield request

    def parse_series(self, response):
        series = response.meta['series']
        # get # of seasons
        ep_widget = response.css('div#title-episode-widget')
        seasons_and_year = ep_widget.css('div.seasons-and-year-nav')
        s_y_list = seasons_and_year.css('div')[0].css('a::text').extract()[:-1]

        # get only seasons, not years
        s_list = [int(x) for x in s_y_list if int(x) < 1000]
        s_list.reverse()

        title_code = series['code']
        url_template = 'http://www.imdb.com{}episodes?season={}'
        for season in s_list:
            url = url_template.format(title_code, season)
            request = scrapy.Request(url=url, callback=self.parse_season)
            request.meta['series'] = series
            yield request

    def parse_season(self, response):
        global db_name
        conn = sqlite3.connect(db_name)
        c = conn.cursor()

        episodes = response.css('div.list_item')
        ep_info = episodes.css('div.info')
        ep_list = ep_info.css('strong').css('a::attr(title)').extract()

        eps = []
        name = response.meta['series']['name']
        parsed_url = ul.urlparse(response.url)
        season = ul.parse_qs(parsed_url.query)['season'][0]
        for ep in enumerate(ep_list, start=1):
            ep_num, ep_name = ep
            e = (name, season, ep_num, ep_name)
            eps.append(e)

        c.executemany('INSERT OR IGNORE INTO tv_series VALUES (?, ?, ?, ?)', eps)
        conn.commit()
        conn.close()
