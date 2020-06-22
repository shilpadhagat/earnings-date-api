import requests
from bs4 import BeautifulSoup
import pymysql
from pymysql.err import OperationalError
import arrow
import time
import os
from flask import escape, jsonify
import json

DB_HOST = os.environ.get("DB_HOST")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
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

def cloud_function_get_earnings(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <http://flask.pocoo.org/docs/1.0/api/#flask.Request>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>.
    """
    if request.method != 'GET':
        return abort(405)

    # Set CORS headers for the main request
    headers = {
        'Access-Control-Allow-Origin': '*'
    }

    request_args = request.args
    if not request_args:
        return "args is invalid, or missing properties", 400, headers
    
    ticker = request_args.get('ticker', None)
    date = request_args.get('date', None)

    if ticker is None and date is None:
        return "ticker and date both cant be null", 400, headers
    elif ticker is not None and date is not None:
        return "Can only provide either ticker or date", 400, headers
    
    if ticker:
        earnings = fetch_earnings_for_ticker(ticker)
    else:
        earnings = fetch_earnings_for_date(date)

    return jsonify(earnings), 200, headers

def fetch_earnings_for_date(date):
    ensure_mysql_conn()
    sql_select_query = """
        SELECT
            c.ticker,
            ed.call_time
        FROM
            companies c
            JOIN earning_dates ed ON c.id = ed.company_id
        WHERE
            ed.call_date = %s
    """

    with __get_cursor() as cursor:
        result = cursor.execute(sql_select_query, (date,))
        result = cursor.fetchall()

    return [
        {
            'ticker': row['ticker'],
            'date': date,
            'time': row['call_time'],
        } 
        for row in result
    ]

def fetch_earnings_for_ticker(ticker):
    ensure_mysql_conn()
    sql_select_query = """
        SELECT
            ed.call_date,
            ed.call_time
        FROM
            companies c
            JOIN earning_dates ed ON c.id = ed.company_id
        WHERE
            c.ticker = %s
    """

    with __get_cursor() as cursor:
        result = cursor.execute(sql_select_query, (ticker,))
        result = cursor.fetchall()    
    
    return [
        {
            'ticker': ticker,
            'date': row['call_date'].strftime('%Y-%m-%d'),
            'time': row['call_time'],
        } 
        for row in result
    ]

def cloud_function_update_earnings(payload, context):
    start = arrow.utcnow().floor('day')
    end = arrow.utcnow().floor('day').shift(days=60)
    while start < end:
        earnings_date_scraper(start.naive)
        start = start.shift(days=1)
    earnings_date_scraper(start.naive)

def earnings_date_scraper(for_date):
    time.sleep(2)
    company_data = []
    # Sending an HTTP request to a URL. Make a GET request to fetch the raw HTML content
    earnings_for_date = for_date.strftime('%Y-%m-%d')
    print('earnings_for_date', earnings_for_date)
    payload = {
        'day': earnings_for_date
    }
    earnings_api_url = "https://finance.yahoo.com/calendar/earnings"
    earnings = requests.get(earnings_api_url, params=payload)
    # Parse the HTML content
    soup = BeautifulSoup(earnings.text, 'html.parser')
    #print('soup', soup)
    results = soup.find(id='cal-res-table')
    print('results', results)
    if not results:
        return
    table = results.find('table', class_="W(100%)")
    print(results)
    table_head = table.find('thead')
    head_row = table_head.find('tr')
    cols = head_row.find_all('th')
    col_names = [ele.text.strip() for ele in cols]
    company_data.append([name for name in col_names if name])

    table_body = table.find('tbody')
    rows = table_body.find_all('tr')
    print(company_data)
    for row in rows:
        row_data = row.find_all('td')
        row_vals = [data.text.strip() for data in row_data]
        company_data.append([val for val in row_vals if val])
    print(company_data)

    for idx, col_name in enumerate(company_data[0]):
        if col_name == 'Symbol':
            ticker_idx = idx
        elif col_name == 'Company':
            company_name_idx = idx
        elif col_name == 'Earnings Call Time':
            earnings_time_idx = idx

    records_to_insert = []
    for datum in company_data[1:]:
        records_to_insert.append([
            get_company_id(datum[ticker_idx], datum[company_name_idx]),
            earnings_for_date,
            datum[earnings_time_idx]
        ])
    print(records_to_insert)
    save_earnings_data(records_to_insert)

def store_companies(ticker, company_name):
    sql_insert_query = """INSERT INTO `companies`
        (`ticker`, `name`)
    VALUES
        (%s, %s)"""

    with __get_cursor() as cursor:
        try:
            cursor.execute(sql_insert_query, (ticker, company_name))
            print (cursor.rowcount, "Record inserted successfully into companies table")
        except:
            pass

def get_company_id(ticker, company_name):
    ensure_mysql_conn()
    sql_select_query = """SELECT `id`
    FROM `companies`
    WHERE `ticker` = %s"""

    with __get_cursor() as cursor:
        result = cursor.execute(sql_select_query, (ticker,))
        result = cursor.fetchone()
    if result:
        return result['id']
    else:
        store_companies(ticker, company_name)
        return get_company_id(ticker, company_name)
    
def save_earnings_data(company_data):
    ensure_mysql_conn()

    earning_dates_list = [data[1] for data in company_data]

    with __get_cursor() as cursor:
        format_strings = ','.join(['%s'] * len(earning_dates_list))
        cursor.execute("DELETE FROM earning_dates WHERE call_date IN (%s)" % format_strings,
            tuple(earning_dates_list))
        print (cursor.rowcount, "Record deleted successfully from earning dates table")

    sql_insert_earnings_date_query = "INSERT INTO earning_dates (company_id, call_date, call_time) VALUES (%s, %s, %s)"

    with __get_cursor() as cursor:
        try:
            result = cursor.executemany(sql_insert_earnings_date_query, company_data)
        except Exception as exc:
            raise RuntimeError("company_data: {}".format(company_data)) from exc
        print (cursor.rowcount, "Record inserted successfully into earning_dates table")

def ensure_mysql_conn():
    global mysql_conn
    if not mysql_conn:
        try:
            mysql_conn = pymysql.connect(**mysql_config)
        except OperationalError:
            print('error')
start_date = arrow.utcnow().floor('day').shift(days=3)
start_date = start_date.naive
#start_date = start_date.strftime('%Y-%m-%d')
print(start_date)
earnings_date_scraper(start_date)