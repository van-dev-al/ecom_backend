from scrapy import signals
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import html


class CellphonesDownloaderMiddleware:
    def __init__(self, driver_path, driver_options):
        self.driver_service = Service(driver_path)
        self.driver_options = driver_options
        self.driver = webdriver.Chrome(service=self.driver_service, options=self.driver_options)

    @classmethod
    def from_crawler(cls, crawler):
        driver_path = crawler.settings.get('SELENIUM_DRIVER_EXECUTABLE_PATH')
        driver_options = webdriver.ChromeOptions()
        for arg in crawler.settings.get('SELENIUM_DRIVER_ARGUMENTS', []):
            driver_options.add_argument(arg)

        middleware = cls(driver_path, driver_options)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware

    def process_request(self, request, spider):
        if 'selenium' in request.meta:
            spider.logger.info(f"Using Selenium to fetch: {request.url}")
            try:
                self.driver.get(request.url)

                # Logic "Load More" with a maximum retry limit
                max_retries = 10  # Limit số lần tải thêm để tránh vòng lặp vô hạn
                retries = 0
                while retries < max_retries:
                    try:
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                        load_more_btn = WebDriverWait(self.driver, 20).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'a.btn-show-more'))
                        )

                        if load_more_btn.is_displayed():
                            spider.logger.info("Clicking 'Load More' button...")
                            self.driver.execute_script("arguments[0].click();", load_more_btn)

                            WebDriverWait(self.driver, 20).until(
                                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.product-info'))
                            )
                            retries += 1
                            spider.logger.info(f"Attempt {retries}: Clicking 'Load More' button...")
                        else:
                            break
                    except Exception as e:
                        spider.logger.info(f"No 'Load More' button found or all products loaded: {e}")
                        break

                body = html.unescape(self.driver.page_source)
                return HtmlResponse(
                    url=self.driver.current_url,
                    body=body,
                    encoding='utf-8',
                    request=request,
                )
            except Exception as e:
                spider.logger.error(f"Error while using Selenium for {request.url}: {e}")
                return HtmlResponse(
                    url=request.url,
                    status=500,
                    request=request,
                )

    def process_response(self, request, response, spider):
        return response

    def process_exception(self, request, exception, spider):
        spider.logger.error(f"Exception during request {request.url}: {exception}")
        return None  # Continue processing exceptions

    def spider_closed(self, spider):
        spider.logger.info("Closing Selenium WebDriver...")
        try:
            self.driver.quit()
        except Exception as e:
            spider.logger.error(f"Error while quitting WebDriver: {e}")
