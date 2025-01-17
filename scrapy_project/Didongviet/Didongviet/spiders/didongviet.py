import random
import time
import scrapy, sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))
import json, pandas as pd, requests
from app.config import Config


class DidongvietSpider(scrapy.Spider):
    name = "didongviet"

    categories = ["3", "5", "6"]
    base_url = "https://didongviet.vn/"
    base_image_url = "https://cdn-v2.didongviet.vn/"

    CATEGORY_MAPPING = {
        'dien-thoai': 'mobiles',
        'may-tinh-bang': 'tablets',
        'apple-macbook-imac': 'laptops',
    }


    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Origin": "https://didongviet.vn",
        "Referer": "https://didongviet.vn/",
    }

    def start_requests(self):
        if os.path.exists(Config.SLUG_ID):
            if os.path.getsize(Config.SLUG_ID) > 0:
                df = pd.read_csv(Config.SLUG_ID)
                if not df.empty:
                    self.logger.info("File cache có dữ liệu. Xóa nội dung và làm mới danh sách slug IDs.")
                    open(Config.SLUG_ID, 'w').close()
            else:
                pass
        else:
            pass

        slug_ids = []
        self.get_slug_ids(slug_ids)

        pd.DataFrame(slug_ids).to_csv(Config.SLUG_ID, index=False, encoding="utf-8-sig")
        self.logger.info(f"Đã lưu {len(slug_ids)} sản phẩm vào file cache.")

        for record in slug_ids:
            slug_category = record["slug_category"]
            slug_id = record['slug_id']
            self.logger.info(f"Lấy dữ liệu cho sản phẩm: {slug_id} - ID: {slug_category}")
            yield scrapy.Request(
                url=f'https://didongviet.vn/_next/data/RdNyWRhq3OlO4ScTFeYFD/{slug_category}/{slug_id}.html.json?slug={slug_category}&id={slug_id}.html',
                headers=self.headers,
                callback=self.parse_response,
                meta={'category': slug_category}
            )
            time.sleep(random.uniform(0.5, 2))

    def get_slug_ids(self, slug_ids):
        max_pages = 3
        for category_id in self.categories:
            for page in range(1, max_pages + 1):
                params = {
                    "page": page,
                    "limit": 10,
                    "category_ids": category_id,
                    "sort_by_outstanding": "true",
                }
                query_string = "&".join(f"{key}={value}" for key, value in params.items())
                url = f"https://ecomws.didongviet.vn/fe/v1/products?{query_string}"

                response = requests.get(url, headers=self.headers)
                if response.status_code == 200:
                    data = response.json().get("data", {}).get("data", [])
                    for record in data:
                        slug_category = record.get("categorySlug")
                        slug_id = record.get("redirect_url")
                        if slug_category and slug_id:
                            slug_ids.append({"slug_category": slug_category, "slug_id": slug_id})
                    time.sleep(1)
                else:
                    self.logger.error(f"Failed to fetch data from {url}, status code: {response.status_code}")

    def parse_response(self, response):
        try:
            data = json.loads(response.text)
            data_seo = data.get("pageProps", {}).get("dataseo", {})
            product = data.get("pageProps", {}).get("product", {})

            if product:
                category = response.meta.get('category')
                category_id = self.CATEGORY_MAPPING.get(category, 'other')

                product_data = {
                    "name": product.get("product_core_name", "N/A"),
                    "current_price": data_seo.get("data", {}).get("price", 0),
                    "original_price": data_seo.get("data", {}).get("list_price", 0),
                    "discount_rate": data_seo.get("data", {}).get("percentage_discount", 0),
                    "review_count": data_seo.get("data", {}).get("review_count", 0),
                    "rating_average": data_seo.get("data", {}).get("rating", 0),
                    "brand": data_seo.get("data", {}).get("brand", "N/A").lower(),

                    "battery": self.get_featues_value(product, "sp_sac_dungluongpin"),
                    "bluetooth": self.get_featues_value(product, "sp_network_bluetooth"),
                    "camera_primary": self.get_featues_value(product, "sp_camerasau_dophangiai"),
                    "camera_secondary": self.get_featues_value(product, "sp_cameratruoc_dophangiai"),
                    "GPU": self.get_featues_value(product, "sp_oscpu_gpu"),
                    "chip_set": self.get_featues_value(product, "sp_oscpu_tocdo"),
                    "NFC": self.get_featues_value(product, "sp_network_other"),
                    "CPU": self.get_featues_value(product, "sp_oscpu_chipset"),
                    "display_type": self.get_featues_value(product, "sp_manhinh_congnghe"),
                    "GPS": self.get_featues_value(product, "sp_network_gps"),
                    "internet": self.get_featues_value(product, "sp_network_net"),
                    "accessories": self.get_featues_value(product, "accessories"),
                    "model": self.get_featues_value(product, "sp_oscpu_os"),
                    "jack_3.5mm": self.get_featues_value(product, "sp_network_jack"),
                    "sim_type": self.get_featues_value(product, "sp_network_sim"),
                    "charging_port": self.get_featues_value(product, "sp_network_connector"),
                    "weight": self.get_featues_value(product, "sp_design_trongluong"),
                    "camera_video": self.get_featues_value(product, "sp_camerasau_quayphim"),
                    "RAM": self.get_featues_value(product, "sp_storage_ram"),
                    "ROM": self.get_featues_value(product, "sp_storage_rom"),
                    "screen_size": self.get_featues_value(product, "sp_manhinh_manhinhrong"),
                    "wifi": self.get_featues_value(product, "sp_network_wifi"),
                }

                source = 'didongviet.vn'
                product_data['source'] = source
                product_data['category'] = category
                product_data['category_id'] = category_id

                url = data_seo.get("data", {}).get("url", None)
                if url:
                    product_data["url"] = self.base_url + url
                else:
                    product_data["url"] = ""

                images = product.get("images", [])
                if images:

                    product_data['image_url'] = [self.base_image_url + image for image in images]
                    product_data['thumbnails'] = [self.base_image_url + images[0]]
                else:
                    product_data['image_url'] = []
                    product_data['thumbnails'] = []
                yield product_data

        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding JSON: {e}")
            self.logger.debug(f"Raw response: {response.text}")

    def get_featues_value(self, product, code):
        try:
            product_features = product.get('productFeatures', [])
            
            for feature in product_features:
                details = feature.get('catalog_feature_details', [])

                for detail in details:
                    current_detail_code = detail.get("detail_code", '').lower()
                    value = detail.get("value", "N/A")

                    if current_detail_code == code.lower():
                        return value
            return 'N/A'
        
        except (IndexError, AttributeError) as e:
            return 'N/A'
