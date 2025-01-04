import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))

import scrapy
import json
import pandas as pd
from app.config import Config


class DropbuySpider(scrapy.Spider):
    name = 'dropbuy'

    base_url = 'https://dropbuy.vn/'
    
    start_urls = ['https://r3.dropbuy.vn/dalon-web-public/categories/categories-all.json']

    def parse(self, response):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        }
        try:
            data = json.loads(response.text)

            ids = []
            
            for category in data:
                category_id = category.get('id', '')
                if category_id:
                    ids.append({'id': category_id})
            
            df = pd.DataFrame(ids)
            df.to_csv(Config.SLUG, index=False, mode='w', header=True)
            self.logger.info(f"Đã lưu {len(ids)} ids vào file CSV.")

            max_page = 2
            for page in range(1, max_page):
                for id in ids:
                    payload = {
                        'category_id' : id['id'],
                        'page_num': page,
                        'page_size': '24',
                        'sort_by_string': 'null'
                    }
                    # payload = {
                    #     "items" : [
                    #         {
                    #             "product_id": 13401,
                    #             "sku": "S735-13401-Freepik06",
                    #             "variation_id": "97db7350-2ebd-4f73-ba53-05b4ea78f264"
                    #         },
                    #         {
                    #             "product_id": 13402,
                    #             "sku": "S735-13402-Freepik07",
                    #             "variation_id": "87da6350-2ebd-4f73-ba53-05b4ea78f212"
                    #         },
                    #         {
                    #             "product_id": 13403,
                    #             "sku": "S735-13403-Freepik08",
                    #             "variation_id": "12db6350-2ebd-4f73-ba53-05b4ea78f223"
                    #         }
                    #     ],
                    # }
                    yield scrapy.Request(
                        url="https://bff.pen.dropbuy.vn/bff/variations/search",
                        method="POST",
                        headers=headers,
                        body=json.dumps(payload),
                        callback=self.parse_products,
                        meta={'id': id, 'page': page}
                    ) 
        except Exception as e:
            pass
            # self.logger.error(f"Lỗi khi parse dữ liệu từ JSON: {str(e)}")

    def parse_products(self, response):
      try:
          data = json.loads(response.text)
          if data.get('success') and 'data' in data:
              products_data = data['data']
              items = products_data.get('items', [])

              results = []

              for item in items:
                  price_data = {
                      "id": item.get('product_id', '')
                  }
                  # url = item.get('slug', '')
                  # p_id = item.get('product_id', '')
                  # if url and p_id:
                  #     price_data['url'] = self.base_url + url + '_p' + str(p_id)

                  results.append(price_data)

              self.logger.info(f"Processing {len(results)} items.")

              pd.DataFrame(results, columns=['id']).to_csv(Config.TEST, index=False, mode='a', header=not pd.io.common.file_exists(Config.TEST))

              # yield scrapy.Request

          else:
              pass
              # self.logger.error("Dữ liệu không hợp lệ hoặc không thành công.")
      
      except json.JSONDecodeError as e:
          pass
          # self.logger.error(f"Error decoding JSON: {e}")
          # self.logger.debug(f"Raw response: {response.text}")

