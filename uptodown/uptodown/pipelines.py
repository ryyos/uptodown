# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import os
import json

from itemadapter import ItemAdapter
from icecream import ic
from .utils import vname

class UptodownPipeline:

    def __init__(self) -> None:
        self.MAIN_PATH = 'data'
        ...

    def __create_dir(self, result: dict) -> str:
        try: os.makedirs(f'{self.MAIN_PATH}/data_raw/uptodown/{result["detail_application"]["platform"]}/{result["detail_application"]["type"]}/{vname(result["reviews_name"].lower())}/json/detail')
        except Exception: ...
        finally: return f'{self.MAIN_PATH}/data_raw/uptodown/{result["detail_application"]["platform"]}/{result["detail_application"]["type"]}/{vname(result["reviews_name"].lower())}/json'
        ...

    def __convert_path(self, path: str) -> str:
        
        path = path.split('/')
        path[1] = 'data_clean'
        return '/'.join(path)
        ...

    def process_item(self, item, spider):

        path = self.__create_dir(item)
        with open(path, 'w', encoding= "utf-8") as file:
            json.dump(item, file, ensure_ascii=False, indent=2, default=str)
        
