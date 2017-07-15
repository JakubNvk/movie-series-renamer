import scrapy
import sqlite3
from bs4 import BeautifulSoup

db_name = '../im.db'


# class Post(scrapy.Item):
    # post_name = scrapy.Field()
    # author = scrapy.Field()
    # points = scrapy.Field()
    # text = scrapy.Field()


class ImdbSpider(scrapy.Spider):
    name = "imdb"
    urls = []

    def __init__(self):
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
        search_res = response.css('tr.findResult')
        affix = search_res.css('a::attr(href)').extract_first()
        url = 'http://www.imdb.com%s' % affix
        # IF movie: parse_movie
        # IF series: parse_series
        yield scrapy.Request(url=url, callback=self.parse_series)

    def parse_series(self, response):
        # get # of seasons
        ep_widget = response.css('div#title-episode-widget')
        seasons_and_year = ep_widget.css('div.seasons-and-year-nav')
        s_y_list = seasons_and_year.css('div')[0].css('a::text').extract()[:-1]

        # get only seasons, not years
        s_list = [int(x) for x in s_y_list if int(x) < 1000]
        s_list.reverse()

        url_template = 'http://www.imdb.com/title/tt1266020/episodes?season={}'
        for season in s_list:
            url = url_template.format(season)
            yield scrapy.Request(url=url, callback=self.parse_season)

    def parse_season(self, response):
        episodes = response.css('div.list_item')
        ep_info = episodes.css('div.info')
        ep_list = ep_info.css('strong').css('a::attr(title)').extract()
