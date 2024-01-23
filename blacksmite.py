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

        items = UptodownItem()

        for url in url_platforms:
            types = Request(url=url, callback=self.__collect_types)
            
            for tipe in types:
                ic(tipe)
                apps = Request(url=tipe, callback=self.__collect_apps)

                for app in apps:
                    details = Request(url=app, callback=self.__parser_app)

                    reviews: List[dict] = Request(url=f'{app}/mng/v2/app/{details["id"]}/comments', callback=self.__extract_review)
                    offset = 10
                    while True:
                        review = Request(url=f'{app}/mng/v2/app/{details["id"]}/comments/unixtime?offset={offset}', callback=self.__exctract_review_api)
                        if not review: break
                        reviews.append(review)

                    for review in reviews:
                        items["link"] = app
                        items["tag"] = ["id.uptodown.com"]
                        items["crawling_time"] = strftime('%Y-%m-%d %H:%M:%S')
                        items["crawling_time_epoch"] = int(time())
                        items["path_data_raw"] = ""
                        items["path_data_clean"] = ""
                        items["reviews_name"] = details["title"]
                        items["location_reviews"] = None
                        items["category_reviews"] = "" # Bro?
                        items["total_reviews"] = details["total_reviews"]
                        items["reviews_rating"] = {
                            "total_rating": details["ratings"],
                            "detail_total_rating": None
                        }
                        items["detail_reviews"] = {
                            "username_reviews": review["username"],
                            "image_reviews": review["avatar"],
                            "created_time": review["posted"],
                            "created_time_epoch": None,
                            "email_reviews": None,
                            "company_name": None,
                            "location_reviews": None,
                            "title_detail_reviews": None,
                            "reviews_rating": review["ratings"],
                            "detail_reviews_rating": None,
                            "total_likes_reviews": review["likes"],
                            "total_dislikes_reviews": None,
                            "total_reply_reviews": "", # Bro?
                            "content_reviews": review["comment"],
                            "reply_content_reviews": "",
                            "date_of_experience": review["posted"],
                            "date_of_experience_epoch": None
                        }
                        items["detail_application"] = details

                        yield reviews


    ...

    def __collect_types(self, response: Response) -> List[str]:
        yield response.css('#main-left-panel-ul-id > div:nth-child(3) div[class="li"] > a ::attr(href)').getall()
        ...
    
    def __collect_apps(self, response: Response) -> List[str]:
        yield response.css('div[class="name"] > a ::attr(href)').getall()
        ...

    def __parser_app(self, response: Response) -> dict:
        body: Response = response.css('div.c1')

        header = {
            "id": body.css('#detail-app-name ::attr(code)'),
            "title": body.css('#detail-app-name ::text'),
            "information": body.css('div.detail > h2 ::text'),
            "version": body.css('div.version ::text'),
            "author": body.css('div.autor ::text'),
            "descriptions": body.css('div.text-description ::text'),
            "total_reviews": body.css('#more-comments-rate-section ::text'),
            "ratings": body.css('#rating ::text'),
            "technical-information": {
                key.css('td:nth-child(2) ::text'): key.css('td:last-child ::text') for key in body.css('#technical-information tbody > tr')
            },
            "previous_version": [
                {
                    "version": prev.css('span.version ::text'),
                    "date": prev.css('span.date ::text'),
                    "sdk": prev.css('span.sdkVersion ::text')
                } for prev in body.css('#versions-items-list > div')
            ]
        }

        yield header

    def __extract_review(self, response: Response) -> List[dict]:
        reviews = Selector(text=response.json()['content'])

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