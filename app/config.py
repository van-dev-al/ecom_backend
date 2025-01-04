import os

class Config:
  SESSION_PERMANENT = False
  SESSION_TYPE = 'filesystem'

  COOKIES_TIKI = {
    "_trackity": "56c90fca-d6dd-16fd-f4ca-2ab9ebfaa71f",
    "_ga": "GA1.1.929809372.1726471035",
    "_gcl_au": "1.1.670789875.1726471040",
    "_fbp": "fb.1.1726471041940.330276232528902538",
    "__uidac": "0166e7db82dd54d4f2dc25f5fcbac095",
    "__R": "1",
    "_hjSessionUser_522327": "eyJpZCI6IjVmMGJkYjQ0LWMzNGMtNWRjMi04MjFlLTJiNmE3MjhiNGIwZSIsImNyZWF0ZWQiOjE3MjY0NzEwNDA5NjYsImV4aXN0aW5nIjp0cnVlfQ==",
    "__tb": "0",
    "__iid": "749",
    "__su": "0",
    "__RC": "4",
    "TOKENS": "{%22access_token%22:%221TyY6HF0JPUg2pin5hajeqmzM3AOxI9R%22}",
    "delivery_zone": "Vk4wMzQwMjQwMTM=",
    "tiki_client_id": "929809372.1726471035",
    "_hjSession_522327": "eyJpZCI6IjJiYjY1YjBjLTdkMTYtNGFiOC1iMjQzLThiNDgzMGNkZjNlNCIsImMiOjE3MzI1NDI2Njg1NzYsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowLCJzcCI6MH0=",
    "__adm_upl": "eyJ0aW1lIjoxNzMyNTQ0NDcwLCJfdXBsIjoiMC0xNTY0NzEwNDIxMTY5OTQ4NzQzIn0=",
    "dtdz": "_PID.3.5a09d385708551e0",
    "_dtdcTime": "1732542670",
    "__IP": "712178135",
    "_ga_S9GLR1RQFJ": "GS1.1.1732542656.17.1.1732542961.56.0.0",
    "cto_bundle": "I-AOUF9zYTZNUFBFSWlrWkFjNE1FU2F4UXEzN1hQSmJ4Z3VlRnBjQUVpUGQ4RW1OT3Z4VEd1Wmw0TE9lTHNZSlhQS0h0Z"
  }
  HEADERS_TIKI = {
      'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
      'Accept': 'application/json, text/plain, */*',
      'Accept-language': 'vi-VN,vi;q=0.9',
      'Referer': 'https://tiki.vn/dien-thoai-smartphone/c1795',
      'x-guest-token': '1TyY6HF0JPUg2pin5hajeqmzM3AOxI9R',
      'Connection': 'keep-alive',
      'TE': 'Trailers',
  }
  PARAMS_TIKI = {
      'platform': 'web',
      'spid': '273258825',
      'version': '3',
  }

  PRODUCT_ID = os.path.abspath(
    os.path.join(
      os.path.dirname(__file__), '..', 'temp', 'product_ids.csv'
    )
  )

  SLUG_ID = os.path.abspath(
    os.path.join(
      os.path.dirname(__file__), '..', 'temp', 'slug_ids.csv'
    )
  )

  SLUG = os.path.abspath(
    os.path.join(
      os.path.dirname(__file__), '..', 'temp', 'slug.csv'
    )
  )

  TEST = os.path.abspath(
    os.path.join(
      os.path.dirname(__file__), '..', 'temp', 'test.csv'
    )
  )
  TEST2 = os.path.abspath(
    os.path.join(
      os.path.dirname(__file__), '..', 'temp', 'test2.csv'
    )
  )

  OUTPUT_DIR = os.path.abspath(
    os.path.join(
      os.path.dirname(__file__), '..', 'output_data'
    )
  )

  PATH = os.path.abspath(
    os.path.join(
      os.path.dirname(__file__), '..', 'scrapy_project'
    )
  )

  PATH_TO_CHOMEDRIVER = os.path.abspath(
    os.path.join(
      os.path.dirname(__file__), '..', 'scrapy_project', 'chromedriver.exe'
    )
  )

  SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:12345@localhost:3306/flaskdb'
  SQLALCHEMY_TRACK_MODIFICATIONS = False