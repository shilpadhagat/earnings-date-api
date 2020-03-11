import sys, requests
from bs4 import BeautifulSoup
import os
import sqlalchemy
import pymysql
from pymysql.err import OperationalError

CONNECTION_NAME = 'poised-lens-267620:us-east1:personalproject1'
DB_HOST = '35.237.194.3'
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASS")
DB_NAME = os.environ.get("DB_NAME")

mysql_config = {
    'host': DB_HOST,
    'user': DB_USER,
    'password': DB_PASSWORD,
    'db': DB_NAME,
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
    'autocommit': True
}

mysql_conn = None

def __get_cursor():
    """
    Helper function to get a cursor
      PyMySQL does NOT automatically reconnect,
      so we must reconnect explicitly using ping()
    """
    try:
        return mysql_conn.cursor()
    except OperationalError:
        mysql_conn.ping(reconnect=True)
        return mysql_conn.cursor()

# [START functions_helloworld_pubsub]
def hello_pubsub():
    """Background Cloud Function to be triggered by Pub/Sub.
    Args:
         event (dict):  The dictionary with data specific to this type of
         event. The `data` field contains the PubsubMessage message. The
         `attributes` field will contain custom attributes if there are any.
         context (google.cloud.functions.Context): The Cloud Functions event
         metadata. The `event_id` field contains the Pub/Sub message ID. The
         `timestamp` field contains the publish time.
    """
    earnings_date_scraper()

# [END functions_helloworld_pubsub]

def earnings_date_scraper():
    data = []
    url = "https://finance.yahoo.com/calendar/earnings?from=2020-02-09&to=2020-02-15&day=2020-02-09"
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    results = soup.find(id='cal-res-table')
    
    table = results.find('table', class_="W(100%)")
    
    table_body = table.find('tbody')

    rows = table_body.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        data.append([ele for ele in cols if ele])
    print(data)
    save_earnings_data(data)

def save_earnings_data(data):
    ensure_mysql_conn()

    sql_insert_query = """INSERT INTO `company`
        (`name`, `ticker`)
    VALUES
        ('abc', 'xyz')
    ON DUPLICATE KEY UPDATE
        `actual` = VALUES(actual)"""

    with __get_cursor() as cursor:
        try:
            result = cursor.executemany(sql_insert_query)
        except Exception as exc:
            raise RuntimeError("company: {}".format(company)) from exc
        print (cursor.rowcount, "Record inserted successfully into actuals table")

def ensure_mysql_conn():
    global mysql_conn

    if not mysql_conn:
        try:
            mysql_conn = pymysql.connect(**mysql_config)
        except OperationalError:
            # If production settings fail, use local development ones
            mysql_config['unix_socket'] = f'/cloudsql/{CONNECTION_NAME}'
            mysql_conn = pymysql.connect(**mysql_config)

hello_pubsub()

