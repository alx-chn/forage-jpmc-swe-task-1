################################################################################
#
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation
#  the rights to use, copy, modify, merge, publish, distribute, sublicense,
#  and/or sell copies of the Software, and to permit persons to whom the
#  Software is furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#  OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.

import csv # working with comma-separated value (CSV) files -> storing and exchanging data in a tabular format
# from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
import http.server # serve HTTP requests, including handling GET and POST requests
import json # encoding and decoding data in JSON
import operator # set of functions for performing common operations on Python objects
import os.path # provides functions for manipulating file paths and directories in a platform-independent way
import re # provides regular expression matching operations
import threading # creating and managing threads in Python, which are used for parallel execution of code
from datetime import timedelta, datetime # provides classes for manipulating dates and times in both simple and complex ways
# from itertools import izip
from random import normalvariate, random # normalvariate generates random numbers from a normal distribution with a specified mean and standard deviation, while random generates random numbers between 0 and 1.
from socketserver import ThreadingMixIn # A mix-in is a way of adding functionality to a class by inheriting from it without defining a new subclass

import dateutil.parser # This module provides functions for parsing dates and times in various formats, including ISO 8601 format

################################################################################
#
# Config

# Sim params

REALTIME = True
SIM_LENGTH = timedelta(days=365 * 5) # The timedelta() constructor creates a timedelta object that represents a duration of time
# set the time when the market opens -> 00:30:00
MARKET_OPEN = datetime.today().replace(hour=0, minute=30, second=0) # The replace() method is used to modify the hour, minute, and second components of the datetime object without changing the other components, such as the year, month, and day

# Market parms
#       min  / max  / std
SPD = (2.0, 6.0, 0.1)  # speed of price change
# Increasing the minimum or maximum value of SPD will make the prices of assets change more quickly or more slowly, respectively. This can affect the volatility of the market and the profitability of different trading strategies.
PX = (60.0, 150.0, 1)  # initial price range
# Granularity refers to the level of detail or precision in a measurement, calculation, or analysis.
# For example, in the PX parameter tuple, the step value is set to 1. This means that the initial price range for the assets in the market can vary by increments of 1
# Decreasing the minimum or maximum value of PX will lower the range of possible initial prices for the assets in the market.
# This can make the market more stable or more volatile, depending on the other parameters.
# A smaller step value in PX will increase the granularity of the initial prices, which can make it easier or harder to find profitable trading opportunities.
FREQ = (12, 36, 50)    # frequency of trades
# The FREQ parameter tuple determines how often trades occur in the market.
# This can affect the liquidity of the market and the effectiveness of different trading strategies. 
# A smaller step value in FREQ will increase the granularity of the frequency, which can make it easier or harder to time trades effectively.
# liquidity: how easily and quickly assets in that market can be bought or sold without significantly affecting their prices
# A market with high liquidity means that there are many buyers and sellers willing to buy or sell assets at any given time, and that trades can be executed quickly and without causing large price movements. In other words, there is a lot of demand for the assets and a lot of supply available, making it easy to buy or sell those assets.
# On the other hand, a market with low liquidity means that there are few buyers and sellers, and that trades can be more difficult and slower to execute. In this case, buying or selling a large amount of assets may cause significant price movements due to the limited supply and demand available.

# Trades

OVERLAP = 4


################################################################################
#
# Test Data

def bwalk(min, max, std):
    """ Generates a bounded random walk. 
        Random walk theory suggests that changes in asset prices are random. 
        This means that stock prices move unpredictably, so that past prices cannot be used to accurately predict future prices
        Random walk theory also implies that the stock market is efficient and reflects all available information. (Efficient market hypothesis)
        (Market efficiency refers to the degree to which market prices reflect all available, relevant information.)

        A: For example, if a company releases a positive earnings report that exceeds analyst expectations, investors may expect the stock price to rise as a result. 

        In an efficient market, the information about an event like A is quickly and accurately reflected in the prices of assets.
        This means that traders and investors may not be able to profitably exploit the information to generate abnormal returns, as the market has already incorporated it into asset prices.
        -> buy index (cuz it refelcts the market) -> not to outperform the market but to match the market

        However, if the market is efficient, the positive earnings report will already be reflected in the current market price of the stock, 
        and any potential increase in the stock price will have already occurred. 
        This means that even if an investor analyzes financial statements and news articles to try to identify undervalued or overvalued stocks, 
        they will not be able to consistently beat the market.

        A random walk challenges the idea that traders can time the market or use technical analysis to identify and profit from patterns or trends in stock prices.
        -> no way to beat or predict the market
        -> The theory thus has important implications for investors, suggesting that buying and holding a diversified portfolio may be the best long-term investment strategy
        -> By accepting that stock prices are unpredictable and efficient, investors can focus on long-term planning and avoid making rash decisions based on short-term market movements
        -> Ultimately, random walk theory reminds investors of the importance of remaining disciplined, patient, and focused on their long-term investment goals.
        -> Info asymmetry: the idea that some market participants have access to more or better information than others4

        FMH: financial markets exhibit patterns that repeat themselves at different scales (or timeframes).
        -> the behavior of the market in the short-term is similar to its behavior in the long-term.
        Fractal: self similarity

        A Black Swan event is an unexpected and rare occurrence that has a severe and widespread impact, often causing significant disruption to society, economy, or financial markets.

        Chaos theory is a mathematical concept that explains that it is possible to get random results from normal equations.

        In finance, the fractal market hypothesis uses the principles of chaos theory to predict the behavior of uncertain markets.
        Chaos theory studies the patterns and regularities that arise from disordered systems.

        *** The fractal market hypothesis suggests that in times of market uncertainty, price movements may move in a fractal pattern rather than a random walk. 
        In other words, the movements that occur on a small time scale may be repeated on a larger scale.

        In finance, the Fractal Market Hypothesis uses elements of chaos theory to predict swings in the stock market.

        Dow Theory

    """
    rng = max - min
    while True:
        max += normalvariate(0, std)
        yield abs((max % (rng * 2)) - rng) + min
        """
            Inside the loop, the yield keyword is used to return the current value of i to the caller.
            When the function is called again, it resumes execution from where it left off, with i holding the next value in the sequence.
        """


def market(t0=MARKET_OPEN):
    """ Generates a random series of market conditions,
        (time, price, spread).
    """
    for hours, px, spd in zip(bwalk(*FREQ), bwalk(*PX), bwalk(*SPD)):
        yield t0, px, spd
        t0 += timedelta(hours=abs(hours))


def orders(hist):
    """ Generates a random set of limit orders (time, side, price, size) from
        a series of market conditions.
        (orders to buy or sell an asset at a specified price or better)
    """
    for t, px, spd in hist:
        stock = 'ABC' if random() > 0.5 else 'DEF'
        side, d = ('sell', 2) if random() > 0.5 else ('buy', -2)
        order = round(normalvariate(px + (spd / d), spd / OVERLAP), 2)
        size = int(abs(normalvariate(0, 100)))
        yield t, stock, side, order, size
        # if return  -> random() always return the same value :( (cuz random is not really random: it's pseudo-random with a seed)


################################################################################
#
# Order Book

def add_book(book, order, size, _age=10):
    """ Add a new order and size to a book, and age the rest of the book. """
    yield order, size, _age # order: price, size: amount of shares, age: how long the order has been in the book
    for o, s, age in book:
        if age > 0:
            yield o, s, age - 1
    """
        The age of an order in an order book represents the amount of time that has elapsed since the order was placed. 
        Orders that have been in the book for a longer period of time are less likely to be filled, 
        since other orders may have been placed at more favorable prices or the market conditions may have moved away from the price of the order.

        By decrementing the age of each order in the book by 1, the add_book function simulates the passage of time and the decreasing likelihood that an order will be filled.
    """

def clear_order(order, size, book, op=operator.ge, _notional=0):
    """ Try to clear a sized order against a book, returning a tuple of
        (notional, new_book) if successful, and None if not.  _notional is a
        recursive accumulator and should not be provided by the caller.
    """
    (top_order, top_size, age), tail = book[0], book[1:]
    if op(order, top_order):
        _notional += min(size, top_size) * top_order
        sdiff = top_size - size
        if sdiff > 0:
            return _notional, list(add_book(tail, top_order, sdiff, age))
        elif len(tail) > 0:
            return clear_order(order, -sdiff, tail, op, _notional)


def clear_book(buy=None, sell=None):
    """ Clears all crossed orders from a buy and sell book, returning the new
        books uncrossed.
    """
    while buy and sell:
        order, size, _ = buy[0]
        new_book = clear_order(order, size, sell)
        if new_book:
            sell = new_book[1]
            buy = buy[1:]
        else:
            break
    return buy, sell


def order_book(orders, book, stock_name):
    """ Generates a series of order books from a series of orders.  Order books
        are mutable lists, and mutating them during generation will affect the
        next turn!
    """
    for t, stock, side, order, size in orders:
        if stock_name == stock:
            new = add_book(book.get(side, []), order, size)
            book[side] = sorted(new, reverse=side == 'buy', key=lambda x: x[0])
        bids, asks = clear_book(**book)
        yield t, bids, asks


################################################################################
#
# Test Data Persistence

def generate_csv():
    """ Generate a CSV of order history. """
    with open('test.csv', 'wb') as f:
        writer = csv.writer(f)
        for t, stock, side, order, size in orders(market()):
            if t > MARKET_OPEN + SIM_LENGTH:
                break
            writer.writerow([t, stock, side, order, size])


def read_csv():
    """ Read a CSV or order history into a list. """
    with open('test.csv', 'rt') as f:
        for time, stock, side, order, size in csv.reader(f):
            yield dateutil.parser.parse(time), stock, side, float(order), int(size)


################################################################################
#
# Server

class ThreadedHTTPServer(ThreadingMixIn, http.server.HTTPServer):
    """ Boilerplate class for a multithreaded HTTP Server, with working
        shutdown.
    """
    allow_reuse_address = True

    def shutdown(self):
        """ Override MRO to shutdown properly. """
        self.socket.close()
        http.server.HTTPServer.shutdown(self)


def route(path):
    """ Decorator for a simple bottle-like web framework.  Routes path to the
        decorated method, with the rest of the path as an argument.
    """

    def _route(f):
        setattr(f, '__route__', path)
        return f

    return _route


def read_params(path):
    """ Read query parameters into a dictionary if they are parseable,
        otherwise returns None.
    """
    query = path.split('?')
    if len(query) > 1:
        query = query[1].split('&')
        return dict(map(lambda x: x.split('='), query))


def get(req_handler, routes):
    """ Map a request to the appropriate route of a routes instance. """
    for name, handler in routes.__class__.__dict__.items():
        if hasattr(handler, "__route__"):
            if None != re.search(handler.__route__, req_handler.path):
                req_handler.send_response(200)
                req_handler.send_header('Content-Type', 'application/json')
                req_handler.send_header('Access-Control-Allow-Origin', '*')
                req_handler.end_headers()
                params = read_params(req_handler.path)
                data = json.dumps(handler(routes, params)) + '\n'
                req_handler.wfile.write(bytes(data, encoding='utf-8'))
                return


def run(routes, host='0.0.0.0', port=8080):
    """ Runs a class as a server whose methods have been decorated with
        @route.
    """

    class RequestHandler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args, **kwargs):
            pass

        def do_GET(self):
            get(self, routes)

    server = ThreadedHTTPServer((host, port), RequestHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    print('HTTP server started on port 8080')
    while True:
        from time import sleep
        sleep(1)
    server.shutdown()
    server.start()
    server.waitForThread()


################################################################################
#
# App

ops = {
    'buy': operator.le, # returns True if its first argument is less than or equal to its second argument
    'sell': operator.ge, # returns True if its first argument is greater than or equal to its second argument
}
"""
    In the context of the trading game server, these operators are used to determine whether a given order is a buy order or a sell order, 
    based on its price and the current state of the order book. When a buy order is placed, 
    it is matched with the best available sell order that has a price less than or equal to the buy order price (using operator.le). 
    
    Similarly, when a sell order is placed, it is matched with the best available buy order 
    that has a price greater than or equal to the sell order price (using operator.ge).
"""


class App(object):
    """ The trading game server application. """

    def __init__(self):
        self._book_1 = dict()
        self._book_2 = dict()
        self._data_1 = order_book(read_csv(), self._book_1, 'ABC')
        self._data_2 = order_book(read_csv(), self._book_2, 'DEF')
        self._rt_start = datetime.now()
        self._sim_start, _, _ = next(self._data_1)
        self.read_10_first_lines()

    @property
    def _current_book_1(self):
        for t, bids, asks in self._data_1:
            if REALTIME:
                while t > self._sim_start + (datetime.now() - self._rt_start):
                    yield t, bids, asks
            else:
                yield t, bids, asks

    @property
    def _current_book_2(self):
        for t, bids, asks in self._data_2:
            if REALTIME:
                while t > self._sim_start + (datetime.now() - self._rt_start):
                    yield t, bids, asks
            else:
                yield t, bids, asks

    def read_10_first_lines(self):
        for _ in iter(range(10)):
            next(self._data_1)
            next(self._data_2)

    @route('/query')
    def handle_query(self, x):
        """ Takes no arguments, and yields the current top of the book;  the
            best bid and ask and their sizes
        """
        try:
            t1, bids1, asks1 = next(self._current_book_1)
            t2, bids2, asks2 = next(self._current_book_2)
        except Exception as e:
            print("error getting stocks...reinitalizing app")
            self.__init__()
            t1, bids1, asks1 = next(self._current_book_1)
            t2, bids2, asks2 = next(self._current_book_2)
        t = t1 if t1 > t2 else t2
        print('Query received @ t%s' % t)
        return [{
            'id': x and x.get('id', None),
            'stock': 'ABC',
            'timestamp': str(t),
            'top_bid': bids1 and {
                'price': bids1[0][0],
                'size': bids1[0][1]
            },
            'top_ask': asks1 and {
                'price': asks1[0][0],
                'size': asks1[0][1]
            }
        },
            {
                'id': x and x.get('id', None),
                'stock': 'DEF',
                'timestamp': str(t),
                'top_bid': bids2 and {
                    'price': bids2[0][0],
                    'size': bids2[0][1]
                },
                'top_ask': asks2 and {
                    'price': asks2[0][0],
                    'size': asks2[0][1]
                }
            }]


################################################################################
#
# Main

if __name__ == '__main__':
    if not os.path.isfile('test.csv'):
        print("No data found, generating...")
        generate_csv()
    run(App())
