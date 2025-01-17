import time, random
import scrapy, requests, pandas as pd, sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))

from app.config import Config

class TikiSpider(scrapy.Spider):
    name = 'tiki'
    CATEGORIES = [
        {'url_key': 'dien-thoai-smartphone', 'category_id': '1795'},
        {'url_key': 'may-tinh-bang', 'category_id': '1794'},
        {'url_key': 'laptop', 'category_id': '8095'},
    ]
    CATEGORY_MAPPING = {
        'dien-thoai-smartphone': 'mobiles',
        'may-tinh-bang': 'tablets',
        'laptop': 'laptops',
    }

    def start_requests(self):
        if os.path.exists(Config.PRODUCT_ID):
            if os.path.getsize(Config.PRODUCT_ID) > 0:
                df = pd.read_csv(Config.PRODUCT_ID)
                if not df.empty:
                    self.logger.info("File cache có dữ liệu. Xóa nội dung và làm mới danh sách product IDs.")
                    open(Config.PRODUCT_ID, 'w').close()
                else:
                    self.logger.info("File cache tồn tại nhưng rỗng. Làm mới danh sách product IDs.")
            else:
                self.logger.info("File cache tồn tại nhưng rỗng. Làm mới danh sách product IDs.")
        else:
            self.logger.info("File cache không tồn tại. Tạo mới và bắt đầu lấy product IDs.")

        product_ids = []
        for category in self.CATEGORIES:
            self.get_product_ids(category['url_key'], category['category_id'], product_ids)
            time.sleep(random.uniform(1, 3))

        pd.DataFrame(product_ids, columns=['id']).to_csv(Config.PRODUCT_ID, index=False)
        self.logger.info(f"Đã lưu {len(product_ids)} product IDs vào file cache.")

        batch_size = 50
        for i in range(0, len(product_ids), batch_size):
            batch = product_ids[i:i + batch_size]
            for product in batch:
                product_id = product['id']
                url_key = product['url_key']
                self.logger.info(f"Lấy dữ liệu cho sản phẩm với ID: {product_id}")
                yield scrapy.Request(
                    url=f'https://tiki.vn/api/v2/products/{product_id}',
                    headers=Config.HEADERS_TIKI,
                    cookies=Config.COOKIES_TIKI,
                    callback=self.parse_product,
                    meta={'url_key': url_key , 'dont_redirect': True}
                )
                time.sleep(random.uniform(0.5, 2))

            time.sleep(random.uniform(0.5, 2))
        
    def get_product_ids(self, url_key, category_id, product_ids):
        params = {
            'limit': '40',
            'include': 'advertisement',
            'aggregations': '2',
            'version': 'home-persionalized',
            'trackity_id': Config.COOKIES_TIKI.get('_trackity', ''),
            'category': category_id,
            'page': '1',
            'src': f'c{category_id}',
            'urlKey': url_key
        }

        max_pages = 3
        for i in range(1, max_pages + 1):
            params['page'] = i
            response = requests.get(
                'https://tiki.vn/api/personalish/v1/blocks/listings',
                headers=Config.HEADERS_TIKI,
                params=params,
                cookies=Config.COOKIES_TIKI,
            )
            if response.status_code == 200:
                data = response.json().get('data', [])
                if not data:
                    self.logger.info(f"Dừng lại ở trang {i}: Không còn dữ liệu.")
                    break
                self.logger.info(f"Thành công lấy product IDs cho trang {i} của danh mục {url_key}")
                for record in data:
                    product_id = record.get('id')
                    if product_id:
                        product_ids.append({'id': product_id,'url_key': url_key})

                time.sleep(1)
            else:
                self.logger.warning(f"Lỗi khi lấy product IDs cho {url_key} trên trang {i}")
                break

    def parse_product(self, response):
        try:
            json_data = response.json()
        except Exception as e:
            self.logger.error(f"Lỗi xảy ra khi parse dữ liệu từ API: {str(e)}")
            return
        
        category = response.meta.get('url_key')
        category_id = self.CATEGORY_MAPPING.get(category, 'other')
        
        product_data = {
            'id': json_data.get('id', None),
            'name': json_data.get('name', 'N/A'),
            'current_price': json_data.get('price', 0),
            'original_price': json_data.get('original_price', 0),
            'discount_rate': json_data.get('discount_rate', 0),
            'review_count': json_data.get('review_count', 0),
            'rating_average': json_data.get('rating_average', 0),

            'battery': self.get_specification_value(json_data, 'battery_capacity', category),
            'bluetooth': self.get_specification_value(json_data, 'bluetooth', category),
            'brand': self.get_specification_value(json_data, 'brand', category).lower(),
            'camera_primary': self.get_specification_value(json_data, 'camera_sau', category),
            'camera_secondary': self.get_specification_value(json_data, 'camera_truoc', category),
            'GPU': self.get_specification_value(json_data, 'chip_do_hoa', category),
            'chip_set': self.get_specification_value(json_data, 'chip_set', category),
            'NFC': self.get_specification_value(json_data, 'connect_nfc', category),
            'CPU': self.get_specification_value(json_data, 'cpu_speed', category),
            'display_type': self.get_specification_value(json_data, 'display_type', category),
            'GPS': self.get_specification_value(json_data, 'gps', category),
            'internet': self.get_specification_value(json_data, 'ho_tro_4g', category),
            'accessories': self.get_specification_value(json_data, 'included_accessories', category),
            'model': self.get_specification_value(json_data, 'item_model_number', category),
            'jack_3.5mm': self.get_specification_value(json_data, 'jack_headphone', category),
            'sim_type': self.get_specification_value(json_data, 'loai_sim', category),
            'charging_port': self.get_specification_value(json_data, 'port_sac', category),
            'weight': self.get_specification_value(json_data, 'product_weight', category),
            'camera_video': self.get_specification_value(json_data, 'quay_phim', category),
            'RAM': self.get_specification_value(json_data, 'ram', category),
            'ROM': self.get_specification_value(json_data, 'rom', category),
            'screen_size': self.get_specification_value(json_data, 'screen_size', category),
            'wifi': self.get_specification_value(json_data, 'wifi', category),
            'url': json_data.get('short_url', None),

        }
        source = 'tiki.vn'
        product_data['source'] = source
        product_data['category'] = category
        product_data['category_id'] = category_id

        images = json_data.get('images', [])
        if images:
            valid_urls = [image.get('base_url', '').strip() for image in images if image.get('base_url')]
            
            if valid_urls:
                product_data['image_url'] = valid_urls
                product_data['thumbnails'] = valid_urls[0]
            else:
                product_data['image_url'] = []
                product_data['thumbnails'] = ''
        else:            
            product_data['image_url'] = []
            product_data['thumbnails'] = ''

        
        yield product_data

    def get_specification_value(self, json_data, code, category=None):
        try:
            specs = json_data.get('specifications', [])
            
            for spec in specs:
                attributes = spec.get('attributes', [])
                
                for attribute in attributes:
                    current_code = attribute.get('code', '').lower()
                    value = attribute.get('value', 'N/A')
                    
                    if category == 'laptop':
                        if current_code == 'dung_luong_dientu' and code.lower() == 'rom':
                            return value
                        elif current_code == 'card_mang_hinh' and code.lower() == 'gpu':
                            return value
                        elif current_code == 'system_requirements' and code.lower() == 'cpu':
                            return value

                    if current_code == code.lower():
                        if value.startswith("<ul>"):
                            selector = scrapy.Selector(text=value)
                            items = selector.css("li::text").getall()
                            value = ';'.join(items)
                        elif value.startswith("<p>"):
                            selector = scrapy.Selector(text=value)
                            items = selector.css("p::text").getall()
                            value = ';'.join(items)

                        return value
            return 'N/A'
        
        except (IndexError, AttributeError) as e:
            return 'N/A'
