import scrapy, sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))

import scrapy
import json
import time, random


class CellphonesSpider(scrapy.Spider):
    name = "cellphones"

    base_url_product = "http://cellphones.com.vn/"
    base_url_image = "https://cdn2.cellphones.com.vn/insecure/rs:fill:358:358/q:90/plain/https://cellphones.com.vn/media/catalog/product"

    categories = ["3", "4", "380"]
    CATEGORY_MAPPING = {
    '3': 'mobiles',
    '4': 'tablets',
    '380': 'laptops',
    }

    price_ranges = [
            {"from": 0, "to": 54990000},
            {"from": 0, "to": 71990000},
            {"from": 0, "to": 194990000},
        ]
    
    def start_requests(self):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Origin": "https://cellphones.com.vn",
            "Referer": "https://cellphones.com.vn/",
        }

        # Duyệt qua các trang (page)
        max_pages = 3
        for category in self.categories:
            for price_range in self.price_ranges:
                for page in range(1, max_pages + 1):
                    payload = {
                        "query": """
                            query GetProductsByCateId {
                                products(
                                    filter: {
                                        static: {
                                            categories: [\"%s\"],
                                            province_id: 30,
                                            stock: { from: 0 },
                                            stock_available_id: [46, 56, 152, 4164],
                                            filter_price: { from: %d, to: %d }
                                        },
                                        dynamic: {}
                                    },
                                    page: %d,
                                    size: 20,
                                    sort: [{ view: desc }]
                                ) {
                                    general {
                                        product_id
                                        name
                                        attributes
                                        sku
                                        doc_quyen
                                        manufacturer
                                        url_key
                                        url_path
                                        categories {
                                            categoryId
                                            name
                                            uri
                                        }
                                        review {
                                            total_count
                                            average_rating
                                        }
                                    },
                                    filterable {
                                        is_installment
                                        stock_available_id
                                        company_stock_id
                                        filter {
                                           id
                                           Label
                                        }
                                        is_parent
                                        exclusive_prices
                                        price
                                        prices
                                        special_price
                                        promotion_information
                                        thumbnail
                                        promotion_pack
                                        sticker
                                        flash_sale_types
                                    }
                                }
                            }
                        """ % (category, price_range["from"], price_range["to"], page),
                        "variables": {}
                    }

                    yield scrapy.Request(
                        url="https://api.cellphones.com.vn/v2/graphql/query",
                        method="POST",
                        headers=headers,
                        body=json.dumps(payload),
                        callback=self.parse_response,
                        meta={
                            "page": page,
                            "category": category,
                            "price_range": price_range
                        },
                    )
                    time.sleep(random.uniform(0.5, 2))

    seen_product_ids = set()
    def parse_response(self, response):
        try:
            data = json.loads(response.text)
            products = data.get("data", {}).get("products", [])

            if not products:
                self.logger.info(f"No more products found on page {response.meta['page']}. Stopping.")
                return

            for product in products:
                general = product.get("general", {})
                filterable = product.get("filterable", {})

                product_id = general.get("product_id", None)
                if product_id in self.seen_product_ids:
                    self.logger.info(f"Product {product_id} đã được xử lý trước đó, bỏ qua.")
                    continue

                self.seen_product_ids.add(product_id)

                category = response.meta.get("category")
                category_id = self.CATEGORY_MAPPING.get(category, 'other')

                product_data = {
                    "product_id": general.get("product_id", None),
                    "name": general.get("name", 'N/A'),
                    "current_price": filterable.get("special_price", 0),
                    "original_price": filterable.get("price", 0),
                    "review_count": general.get("review", {}).get("total_count", 0),
                    "rating_average": general.get("review", {}).get("average_rating", 0),

                    "battery": general.get("attributes", {}).get("battery", "N/A"),
                    "bluetooth": general.get("attributes", {}).get("bluetooth", "N/A"),
                    "brand": general.get("attributes", {}).get("manufacturer", "N/A").lower(),
                    "camera_primary": general.get("attributes", {}).get("camera_primary", "N/A"),
                    "camera_secondary": general.get("attributes", {}).get("camera_secondary", "N/A"),
                    "GPU": general.get("attributes", {}).get("gpu", "N/A"),
                    "chip_set": general.get("attributes", {}).get("chipset","N/A"),
                    "NFC": general.get("attributes", {}).get("mobile_nfc", "N/A"),
                    "CPU": general.get("attributes", {}).get("cpu", "N/A"),
                    "display_type": general.get("attributes",{}).get("mobile_type_of_display", "N/A"),
                    "GPS": general.get("attributes",{}).get("gps", "N/A"),	
                    "internet": general.get("attributes",{}).get("loai_mang", "N/A"),
                    "accessories": general.get("attributes",{}).get("included_accessories", "N/A"),	
                    "model": general.get("attributes",{}).get("thumbnail_label", "N/A"),
                    "jack_3.5mm": general.get("attributes",{}).get("mobile_jack_tai_nghe", "N/A"),
                    "sim_type": general.get("attributes",{}).get("sim", "N/A"),
                    "charging_port": general.get("attributes",{}).get("mobile_cong_sac", "N/A"),
                    "weight": general.get("attributes",{}).get("product_weight", "N/A"),
                    "camera_video": general.get("attributes",{}).get("camera_video", "N/A"),
                    "RAM": general.get("attributes",{}).get("mobile_ram_filter", "N/A"),
                    "ROM": general.get("attributes",{}).get("mobile_storage_filter", "N/A"),
                    "screen_size": general.get("attributes",{}).get("display_size", "N/A"),
                    'wifi': general.get("attributes",{}).get("wlan", "N/A"),
                }

                source = 'cellphones.com.vn'
                product_data['source'] = source
                product_data['category'] = category
                product_data['category_id'] = category_id
                
                discount_rate = 0
                if isinstance(filterable, dict):
                    exclusive_prices = filterable.get("exclusive_prices")
                    if isinstance(exclusive_prices, dict):
                        smem = exclusive_prices.get("SMem")
                        if isinstance(smem, dict):
                            discount_rate = smem.get("total_discount_percent", 0)

                product_data["discount_rate"] = discount_rate


                url_path = general.get("url_path", None)
                if url_path:
                    product_data["url"] = self.base_url_product + url_path
                else:
                    product_data["url"] = "" 

                image_path = general.get("attributes", {}).get("image", None)
                thumnails = general.get("attributes", {}).get("image", None)

                if image_path:
                    product_data["image_url"] = self.base_url_image + image_path
                    product_data["thumbnails"] = self.base_url_image + thumnails
                else:
                    product_data["image_url"] = []
                    product_data["thumbnails"] = []

                yield product_data
        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding JSON: {e}")
            self.logger.debug(f"Raw response: {response.text}")
            
