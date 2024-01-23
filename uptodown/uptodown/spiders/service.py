import scrapy

from typing import List
from icecream import ic
from time import strftime, time

from scrapy.http import Response
from scrapy.http import Request
from scrapy.selector import Selector
from scrapy.http import request
from uptodown.items import UptodownItem

class ServiceSpider(scrapy.Spider):
    name = "service"
    # allowed_domains = ["id.uptodown.com"]
    start_urls = ["https://id.uptodown.com"]
    
    _platforms = ['andorid', 'windows', 'mac']

# https://miui-security.id.uptodown.com/mng/v2/app/732541/comments

    def parse(self, response: Response):
        url_platforms = response.css('#platform-item > a ::attr(href)').getall()

        self.items = UptodownItem()

        for url in url_platforms:
            yield Request(url=url, callback=self.__collect_types)

    ...

    def __collect_types(self, response: Response) -> List[str]:
        for type in response.css('#main-left-panel-ul-id > div:nth-child(3) div[class="li"] > a ::attr(href)').getall():
            yield Request(url=type, callback=self.__collect_apps)
        ...
    
    def __collect_apps(self, response: Response) -> List[str]:
        for app in response.css('div[class="name"] > a ::attr(href)').getall():
            yield Request(url=app, callback=self.__parser_app)
        ...

    def __parser_app(self, response: Response) -> dict:
        body: Response = response.css('div.c1')

        ic(response.url)

        header = {
            "id": body.css('#detail-app-name ::attr(code)').get(),
            "title": body.css('#detail-app-name ::text').get(),
            "information": body.css('div.detail > h2 ::text').get(),
            "url": response.url,
            "version": body.css('div.version ::text').get(),
            "author": body.css('div.autor a ::text'),
            "descriptions": body.css('div.text-description p::text').extract(),
            "total_reviews": body.css('#more-comments-rate-section ::text').extract()[-1].strip(),
            "ratings": body.css('#rating ::text').get().strip(),
            "technical-information": {
                key.css('td:nth-child(2) ::text').get().strip(): key.css('td:last-child ::text').get().strip() for key in body.css('#technical-information tr')
            },
            "previous_version": [
                {
                    "version": prev.css('span.version ::text').get(),
                    "date": prev.css('span.date ::text').get(),
                    "sdk": prev.css('span.sdkVersion ::text').get()
                } for prev in body.css('#versions-items-list > div')
            ]
        }

        yield Request(url=f'{header["url"]}/mng/v2/app/{header["id"]}/comments', callback=self.__extract_review, cb_kwargs=header)

    def __extract_review(self, response: Response, **kwargs) -> List[dict]:
        reviews = Selector(text=response.json()['content'])

        ic(kwargs)

        for review in reviews.css('div.comment'):
            yield {
                "username": review.css('span.user ::text'),
                "avatar": review.css('img')[0].attrib('src'),
                "posted": review.css('span')[0].get(),
                "ratings": len(review.css('img.active')),
                "likes": review.css('div.favs-icon ::text'),
                "comment": review.css('p ::text')
            }

        ...

    def __exctract_review_api(self, response: Response):
        reviews = response.json()

        if reviews["success"]:
            for review in reviews["data"]:
                yield {
                    "username": review["userName"],
                    "avatar": review["icon"],
                    "posted": review["timeAgo"],
                    "ratings": review["rating"],
                    "likes": review["likes"],
                    "comment": review["text"]
                }
        else:
            yield False
        ...