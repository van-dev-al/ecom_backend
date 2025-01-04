from app.config import Config
import os, sys
import threading
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy_project.Tiki.Tiki.spiders.tiki import TikiSpider
from scrapy_project.Cellphones.Cellphones.spiders.cellphones import CellphonesSpider
from scrapy_project.Cellphones.Cellphones.spiders.sforum import SforumSpider
from scrapy_project.Didongviet.Didongviet.spiders.didongviet import DidongvietSpider
from datetime import datetime

available_spiders = {
    "tiki": TikiSpider,
    "cellphones": CellphonesSpider,
    "didongviet": DidongvietSpider,
    "sforum": SforumSpider
}

scrapy_status = {
    spider_name: {"running": False, "log": ""}
    for spider_name in available_spiders.keys()
}
lock = threading.Lock()

def run_spider(spider_name):
    try:
        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        output_file = os.path.join(Config.OUTPUT_DIR, f"{spider_name}_{timestamp}.csv")

        print(f"Saving output to: {output_file} -------------------------------------------------------------------------------------------------------")

        with lock:
            scrapy_status[spider_name]["running"] = True
            scrapy_status[spider_name]["log"] = f"Spider {spider_name} started..."

        settings = get_project_settings()
        settings.set("FEED_URI", f"file:///{output_file.replace(os.sep, '/')}")
        settings.set("FEED_FORMAT", "csv")
        settings.set("FEED_EXPORT_ENCODING", "utf-8")
        
        process = CrawlerProcess(settings)
        process.crawl(available_spiders[spider_name], output=output_file)
        process.start()

    except Exception as e:
        with lock:
            scrapy_status[spider_name]["log"] = f"error {str(e)}"

    finally:
        with lock:
            scrapy_status[spider_name]["running"] = False
            scrapy_status[spider_name]["log"] = f"Spider {spider_name} crawl done!"

def get_latest_csv_files(spider_names):
    output_dir = Config.OUTPUT_DIR
    if not os.path.exists(output_dir):
        return {"status": "error", "message": "Output directory does not exist."}, 400

    csv_files = [
        filename for filename in os.listdir(output_dir)
        if filename.endswith('.csv')
    ]

    files_with_dates = []
    for file in csv_files:
        try:
            timestamp_str = "_".join(file.split('_')[-2:]).replace('.csv', '')
            timestamp = datetime.strptime(timestamp_str, "%d-%m-%Y_%H-%M-%S")
            files_with_dates.append((file, timestamp))
        except ValueError as e:
            print(f"Skipping file: {file}, Error: {e}")

    if not files_with_dates:
        return {"status": "error", "message": "No valid CSV files found with timestamps."}, 400

    files_with_dates.sort(key=lambda x: x[1], reverse=True)

    result_files = {}
    for file, timestamp in files_with_dates:
        spider_name = file.split('_')[0]
        if spider_name in spider_names:
            if spider_name not in result_files:
                result_files[spider_name] = {
                    "file": file,
                    "timestamp": timestamp.strftime("%d-%m-%Y %H:%M:%S")
                }
    return {"status": "success", "latest_files": result_files}, 200

def get_latest_products_csv_files():
    return get_latest_csv_files(['tiki', 'cellphones', 'didongviet'])

def get_latest_new_csv_files():
    return get_latest_csv_files(['sforum'])