import csv
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from flask import Blueprint, render_template, request, jsonify

from app.config import Config
from app.scrapy_integration.run_scrapy import scrapy_status, available_spiders, lock, run_spider, get_latest_new_csv_files, get_latest_products_csv_files, get_latest_csv_files

from multiprocessing import Process
import random

api = Blueprint('api', __name__)

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
    # Lấy danh sách các tệp CSV
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