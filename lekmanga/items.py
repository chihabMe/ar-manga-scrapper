# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class LekmangaItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class MangaImageItem(scrapy.Item):
    image_urls = scrapy.Field()
    images = scrapy.Field()  # Needed by ImagesPipeline to store the results
    chapter = scrapy.Field()
    manga_name  = scrapy.Field()
