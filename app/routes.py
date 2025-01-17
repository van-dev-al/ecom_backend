import csv
import os, sys
import random
# from difflib import SequenceMatcher
from fuzzywuzzy import fuzz
from unidecode import unidecode
import re
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from flask import Blueprint, render_template, request, jsonify

from app.config import Config
from app.scrapy_integration.run_scrapy import scrapy_status, available_spiders, lock, run_spider, get_latest_new_csv_files, get_latest_products_csv_files, get_latest_csv_files

from multiprocessing import Process

api = Blueprint('api', __name__)

def clean_string(text):
    # Chuẩn hóa và loại bỏ các ký tự đặc biệt
    text = unidecode(text.lower())  # Chuẩn hóa và chuyển thành chữ thường
    text = re.sub(r'[^a-z0-9\s]', '', text)  # Loại bỏ ký tự không phải chữ cái hoặc số
    return text

@api.route('/')
def index():
    spiders = available_spiders.keys()
    return render_template(
        'index.html', 
        title="Ecom API", 
        spider=spiders, 
        scrapy_status=scrapy_status
    )

@api.route('/crawl/<spider_name>', methods=['GET'])
def crawl_spider(spider_name):
    if spider_name not in available_spiders:
        return jsonify({
            "status": "error",
            "message": f"Spider '{spider_name}' do not exist.",
        }), 400

    with lock:
        if scrapy_status[spider_name]["running"]:
            return jsonify({
                "status": "error",
                "message": f"Spider '{spider_name}' is Running!.",
            }), 400
        scrapy_status[spider_name]["running"] = True
        scrapy_status[spider_name]["log"] = "Spider is runned."


    process = Process(target=run_spider, args=(spider_name,))
    process.start()

    return jsonify({
        "status": "success",
        "message": f"Spider '{spider_name}' added.",
    }), 200

@api.route('/latest_products_data', methods=['GET'])
def latest_product_data():
    sources = request.args.get('source')
    categories = request.args.get('categories')
    sort_by = request.args.get('sortBy')
    page = request.args.get('page')
    page_size = request.args.get('pageSize')
    search_query = request.args.get('searchQuery')
    search_name_query = request.args.get('searchNameQuery')

    result, status_code = get_latest_products_csv_files()
    if result["status"] == "error":
        return jsonify(result), status_code

    latest_files = result["latest_files"]
    output_dir = Config.OUTPUT_DIR
    data = []

    for spider_name, file_info in latest_files.items():
        file_path = os.path.join(output_dir, file_info["file"])
        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    data.append({"spider": spider_name, "data": row})
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return jsonify({"status": "error", "message": f"Error reading file {file_path}"}), 500
    random.shuffle(data)
    
    if sources:
        sources_list = sources.split(',')
        data = [item for item in data if item['data']['source'] in sources_list]

    if categories:
        categories_list = categories.split(',')
        data = [item for item in data if item['data']['category_id'] in categories_list]
    
    if search_name_query:
        search_name_cleaned = search_name_query.lower()
        data = [
            item for item in data 
            if search_name_cleaned in item['data']['name'].lower()
        ]

    if search_query:
        search_query_cleaned = search_query.lower()
        search_query_cleaned = search_query_cleaned.replace("chính hãng", "").replace("hàng chính hãng", "") \
            .replace("điện thoại", "").replace("VN/A", "").replace("|", "").replace("(", "") \
            .replace(")", "").replace("/", "").replace("-", "").replace("+", "") \
            .replace("chỉ có tại cellphones", "").replace("(cty)","").replace("wifi","").strip()

        filtered_data = []
        filtered_two_word_names = []
        filtered_three_word_names = []
        filtered_four_word_names = []

        for item in data:
            product_name = item['data']['name'].lower()
            product_name_cleaned = product_name.replace("chính hãng", "").replace("hàng chính hãng", "") \
            .replace("điện thoại", "").replace("VN/A", "").replace("|", "").replace("(", "") \
            .replace(")", "").replace("/", "").replace("-", "").replace("+", "") \
            .replace("chỉ có tại cellphones", "").replace("(cty)","").replace("wifi","").strip()

            word_count = len(product_name_cleaned.split())
            common_count, _ = common_word_count(search_query_cleaned, product_name_cleaned)

            if word_count == 3 and common_count >= 2:
                filtered_two_word_names.append(item)
            # elif word_count == 4 and common_count >= 2:
            #     filtered_three_word_names.append(item)
            # elif word_count == 5 and common_count >= 3:
            #     filtered_four_word_names.append(item)
            elif common_count >= 4:
                similarity_score = fuzz.token_sort_ratio(search_query_cleaned, product_name_cleaned)
                if similarity_score >= 60:
                    filtered_data.append(item)

        data = filtered_data + filtered_two_word_names + filtered_three_word_names + filtered_four_word_names

    if sort_by:
        if sort_by == 'current_price_asc':
            data = sorted(data, key=lambda p: float(p['data']['current_price']) if 'current_price' in p['data'] else float('inf'))
        elif sort_by == 'current_price_desc':
            data = sorted(data, key=lambda p: float(p['data']['current_price']) if 'current_price' in p['data'] else float('-inf'), reverse=True)
        elif sort_by == 'name':
            data = sorted(data, key=lambda p: p['data']['name'])
        elif sort_by == 'discount_rate':
            data = sorted(data, key=lambda p: float(p['data']['discount_rate']) if 'discount_rate' in p['data'] else 0, reverse=True)
        elif sort_by == 'review_count':
            data = sorted(data, key=lambda p: int(p['data']['review_count']) if 'review_count' in p['data'] else 0, reverse=True)
        else:
            return jsonify({"status": "error", "message": "Invalid sort option"}), 400

    if page and page_size:
        try:
            page = int(page)
            page_size = int(page_size)
        except ValueError:
            return jsonify({"status": "error", "message": "Page and pageSize must be integers."}), 400

        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        data = data[start_index:end_index]

    return jsonify({"status": "success", "data": data}), 200

def common_word_count(str1, str2):
    words1 = set(str1.lower().split())
    words2 = set(str2.lower().split())
    
    common_words = words1.intersection(words2)
    return len(common_words), common_words

@api.route('/latest_news_data', methods=['GET'])
def latest_news_data():
    result, status_code = get_latest_new_csv_files()
    if result["status"] == "error":
        return jsonify(result), status_code

    latest_files = result["latest_files"]
    output_dir = Config.OUTPUT_DIR
    data = []

    for spider_name, file_info in latest_files.items():
        file_path = os.path.join(output_dir, file_info["file"])
        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    data.append({"spider": spider_name, "data": row})
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return jsonify({"status": "error", "message": f"Error reading file {file_path}"}), 500

    return jsonify({"status": "success", "data": data}), 200


@api.route('/latest_csv_files', methods=['GET'])
def latest_csv_files():
    result, status_code = get_latest_csv_files(['tiki', 'cellphones', 'didongviet', 'sforum'])
    if result["status"] == "error":
        return jsonify(result), status_code

    latest_files = result["latest_files"]
    return jsonify({"status": "success", "latest_files": latest_files}), 200


@api.route('/latest_all_data', methods=['GET'])
def latest_all_data():
    product_result, product_status_code = get_latest_products_csv_files()
    if product_result["status"] == "error":
        return jsonify(product_result), product_status_code

    news_result, news_status_code = get_latest_new_csv_files()
    if news_result["status"] == "error":
        return jsonify(news_result), news_status_code

    all_data = {
        "products": product_result["latest_files"],
        "news": news_result["latest_files"]
    }

    return jsonify({"status": "success", "all_data": all_data}), 200