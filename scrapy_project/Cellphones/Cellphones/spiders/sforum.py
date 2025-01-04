from datetime import datetime
import scrapy, requests, pandas as pd, sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))

import scrapy
import json

from app.config import Config


class SforumSpider(scrapy.Spider):
    name = "sforum"

    base_image_url_sforum = "https://cellphones.com.vn/sforum/"

    def start_requests(self):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Origin": "https://cellphones.com.vn",
            "Referer": "https://cellphones.com.vn/",
        }

        # Duyệt qua các trang (page)
        max_pages = 4
        for page in range(1, max_pages + 1):
            payload = {
                "query": """
                    query Posts {
                        posts(
                            filter: { include: {categories: [7095]}  } 
                            paginator: {size:6 , page: %d}
                            sort: [ { field: \"published_at\", direction: \"desc\" } ]
                        ) {
                            posts {
                                id
                                title
                                slug
                                thumbnail
                                short_description
                                published_at
                                extra_attribute
                                author {
                                    id
                                    first_name
                                    last_name
                                    slug
                                }
                            }
                            meta {
                                total_items
                                total_pages
                                current_page
                                page_size
                            }
                        }
                    }
                """ % page ,
                "variables": {}
            }
            
            yield scrapy.Request(
                url="https://api.sforum.vn/graphql/query",
                method="POST",
                headers=headers,
                body=json.dumps(payload),
                callback=self.parse_response,
                meta={
                    "page": page,
                },
            )


    def parse_response(self, response):
        try:
            data = json.loads(response.text)
            posts = data.get("data", {}).get("posts", {}).get("posts", [])

            if not posts:
                self.logger.info(f"No more posts found on page {response.meta['page']}. Stopping.")
                return

            for post in posts:
                product_data = {
                    "title": post.get("title", ""),
                    "author": f"{post.get('author', {}).get('first_name', '')} {post.get('author', {}).get('last_name', '')}".strip(),
                    "description": post.get("short_description", ""),
                    "image_url": post.get("thumbnail", ""),
                    "url": self.base_image_url_sforum + post.get("slug", ""),
                }
                product_data["category_id"] = "news"

                published_at = post.get("published_at", "")
                if published_at:
                    try:
                        dt_obj = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                        product_data["published"] = dt_obj.strftime("%d/%m/%Y %H:%M:%S")
                    except ValueError:
                        product_data["published"] = published_at

                yield product_data

        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding JSON: {e}")
            self.logger.debug(f"Raw response: {response.text}")
            
