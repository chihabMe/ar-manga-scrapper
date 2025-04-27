import os
import scrapy
from scrapy.pipelines.images import ImagesPipeline
from scrapy import Request
from scrapy.exceptions import DropItem
import psycopg2
from dotenv import load_dotenv
import json
load_dotenv()

class DatabasePipeline():
    def open_spider(self, spider):
        self.conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        self.cursor = self.conn.cursor()
        self.create_tables()
        
    def create_tables(self):
        self.cursor.execute("""
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";  -- Enables UUID generation
        """)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS mangas (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),  -- UUID primary key
            name VARCHAR UNIQUE NOT NULL
        );
        """)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS chapters (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),  -- UUID primary key
            manga_id UUID REFERENCES mangas(id) ON DELETE CASCADE,  -- Foreign key to mangas
            chapter_number INT NOT NULL,
            images JSONB,  -- Storing images as a JSONB array (list of strings)
            is_done BOOLEAN DEFAULT FALSE
        );
        """)
        self.conn.commit()
        
    def process_item(self, item, spider):
        manga_id = self.insert_manga(item)
        if manga_id:
            self.insert_chapter(manga_id, item)
        return item
        
    def insert_manga(self, item):
        insert_manga_query = """
            INSERT INTO mangas (name) VALUES (%s) ON CONFLICT (name) DO NOTHING RETURNING id;
        """
        self.cursor.execute(insert_manga_query, (item.get("manga_name"),))
        manga_id = self.cursor.fetchone()
        if manga_id:
            return manga_id[0]
        else:
            self.cursor.execute("SELECT id FROM mangas WHERE name = %s", (item.get('manga_name'),))
            manga_id = self.cursor.fetchone()
            if manga_id:
                return manga_id[0]
        return None
        
    def insert_chapter(self, manga_id, item):
        # Insert chapter data
        insert_chapter_query = """
        INSERT INTO chapters (manga_id, chapter_number, images)
        VALUES (%s, %s, %s);
        """
        chapter = int(item.get('chapter'))
        images = json.dumps(item.get('image_urls'))
        self.cursor.execute(insert_chapter_query, (manga_id, chapter, images))
        self.conn.commit()
        
    def is_chapter_done(self,manga_name,chapter_number):
        self.cursor.execute("SELECT id FROM mangas WHERE name = %s", (manga_name,))
        manga_id = self.cursor.fetchone()
        if manga_id:
            # Update the chapter status
            select_query = """
            SELECT is_done FROM  chapters 
            WHERE manga_id = %s AND chapter_number = %s;
            """
            self.cursor.execute(select_query, (manga_id[0], chapter_number))
            is_done = self.cursor.fetchone()
            if is_done:
                return is_done[0]
        return False


    def mark_chapter_as_done(self, manga_name, chapter_number):
        # First get the manga ID
        self.cursor.execute("SELECT id FROM mangas WHERE name = %s", (manga_name,))
        manga_id = self.cursor.fetchone()
        if manga_id:
            # Update the chapter status
            update_query = """
            UPDATE   chapters  SET is_done = True 
            WHERE manga_id = %s AND chapter_number = %s;
            """
            self.cursor.execute(update_query, (manga_id[0], chapter_number))
            self.conn.commit()
            return True
        return False
        
        if manga_id:
            # Update the chapter status
            update_query = """
            UPDATE chapters SET is_done = TRUE 
            WHERE manga_id = %s AND chapter_number = %s;
            """
            self.cursor.execute(update_query, (manga_id[0], chapter_number))
            self.conn.commit()
            return True
        return False
        
    def close_spider(self, spider):
        # Close the database connection
        self.cursor.close()
        self.conn.close()

class CleanDataPipeline():
    def process_item(self, item, spider):
        for field, value in item.items():
            if isinstance(value, str):
                value = value.strip()
            if field == "manga_name":
                value = value.replace("-", "_")
            item[field] = value
        return item

class OrderedImagesPipeline(ImagesPipeline):
    def get_media_requests(self, item, info):

        db_pipeline = info.spider.crawler.engine.scraper.itemproc.middlewares[1]
        if isinstance(db_pipeline, DatabasePipeline):
            # Mark the chapter as done after all images are downloaded
            is_done = db_pipeline.is_chapter_done(item['manga_name'], int(item['chapter']))
            if is_done:
                return 
        for image_url in item['image_urls']:
            yield scrapy.Request(image_url)
            
    def file_path(self, request, response=None, info=None, *, item=None):
        print("-----------filepath-----------------")
        print(info)
        if response:
            db_pipeline = info.spider.crawler.engine.scraper.itemproc.middlewares[1]
            print("------------------db pipeline-------")
            print(db_pipeline)
            if isinstance(db_pipeline, DatabasePipeline):
                print("entered")
                # Mark the chapter as done after all images are downloaded
                db_pipeline.mark_chapter_as_done(item['manga_name'], int(item['chapter']))
            
        print(response)
        print("=====================")
        image_name = request.url.split("/")[-1]
        chapter = item["chapter"]
        manga_name = item["manga_name"].replace("-", "_")
        image_filename = f"{manga_name}/{chapter}/{image_name}"
        return image_filename
    #
    # def item_completed(self, results, item, info):
    #     print("------------running item completed ----------")
    #     print(item)
    #     print(info)
    #     print("==================================")
    #     image_paths = [x['path'] for ok, x in results if ok]
    #     if not image_paths:
    #         raise DropItem("Item contains no images")
    #
    #     item['image_paths'] = image_paths
    #
        # Get access to the database pipeline to mark the chapter as done
        return item
