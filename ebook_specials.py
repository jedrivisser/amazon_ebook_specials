#!/usr/bin/python

import urllib
import urllib2
import unicodedata
import cookielib
import re
import ConfigParser
import os

from bs4 import BeautifulSoup


class EbookSpecials:
    """
    Amazon e-book Specials checker

    This program checks for books by <authors> (using their amazon ID) which
    cost less than <price> and filters out all books in <ignore>.
    You can overwrite <price> for a specific book by adding its name and value
    to the <overwrite> dictionary

    """

    def __init__(self):
        # Instance attributes set by config
        self.max_price = None
        self.login = None
        self.email = None
        self.password = None
        self.use_proxy = None
        self.proxy = None
        self.authors = None
        self.ignore = None
        self.own = None
        self.overwrite = None
        self.books = None

        self.load_config()

        # Set up proxy, opener and cookies ####################################
        cj = cookielib.CookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        self.opener.addheaders = [('User-Agent',
                                   'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:26.0) Gecko/20100101 Firefox/26.0'), ]
        if self.use_proxy:
            self.opener.add_handler(
                urllib2.ProxyHandler({"https": self.proxy, "http": self.proxy}))

        if self.login:
            self.log_in()

        # Go through whole list of authors and call getPage() for each result
        # page for each author ################################################
        message = unicode('')
        for authorID in self.authors:
            # Run once to get first page and a page count #####################
            result = self.check_page(authorID)
            if result:
                m, pages, more = result
                message += unicode(m)
                # Run for the other pages if more than one needs to be loaded
                for page in range(2, pages + 1):
                    if more:
                        m, more = self.check_page(authorID, page)
                        message += unicode(m)
            else:
                print "Could not connect"
                return

        for bookID in self.books.keys():
            max_book_price = self.max_price if float(
                self.books[bookID]) < 0 else float(self.books[bookID])
            m = self.check_book(bookID, max_book_price)
            message += unicode(m)

        message = unicodedata.normalize('NFKD', message).encode('ascii', 'ignore')
        if message == '':
            message = "No books cheaper than $" + str(self.max_price)
        print "======e-books cheaper than $" + str(self.max_price) + "======\n" + message

    def check_page(self, author_id, page=1):
        """
        Checks one page for specials and returns the found specials,
        the number of pages, and if you should look for more specials.

        """

        url = "http://www.amazon.com/r/e/" + author_id + \
              "/?rh=n%3A283155%2Cp_n_feature_browse-bin%3A618073011&sort=price&page=" + str(page)

        try:
            data = str(self.opener.open(url).read())
        except urllib2.HTTPError, e:
            print e.code
            print e.read()
            return None

        soup = BeautifulSoup(data, "html.parser")

        books = soup("div", {"id": re.compile('result_.*')})
        message = ""
        more = True
        for book in books:
            book_id = book['name']
            name = book('h3')[0]('a')[0].string

            link = "http://www.amazon.com/dp/" + book_id
            prices = book('div', 'tp')[0]('table')[0]('tr')[1]('td')[2]('a')
            # needed to ignore kindleUnlimited $0.00
            price_string = prices[len(prices) - 1].string
            price_float = float(price_string[1:])
            if price_float < self.max_price:
                if book_id in self.ignore or book_id in self.own:
                    continue
                elif book_id in self.overwrite:
                    if price_float < float(self.overwrite[book_id]):
                        message += name + " " + price_string + " - " + link + "\n"
                else:
                    message += name + " " + price_string + " - " + link + "\n"
            else:
                # sets more to false if prices on page go above 'max_price'
                more = False

        if page == 1:
            if soup('span', "pagnDisabled"):
                pages = int(soup('span', "pagnDisabled")[0].string)
            elif soup('span', "pagnLink"):
                pages = int(soup('span', "pagnLink")[-1].string)
            else:
                pages = 1
            return message, pages, more
        else:
            return message, more

    def check_book(self, book_id, max_price):
        """Check price of specific book from the [BOOKS] section"""

        url = "http://www.amazon.com/dp/" + book_id
        try:
            data = str(self.opener.open(url).read())
        except urllib2.HTTPError, e:
            print e.code
            print e.read()
            return None

        soup = BeautifulSoup(data, "html.parser")

        name = soup.title.string[12:-14]
        price = soup("div", "buying", id="priceBlock")[
            0](True, 'priceLarge')[0].string.strip()
        dprice = float(price[1:])
        message = ""
        if dprice < max_price:
            message = name + " " + price + " - " + url + "\n"
        return message

    def log_in(self):
        """Log-in to you amazon account"""

        # Get and set form params #############################################
        url_login_page = "https://www.amazon.com/ap/signin/182-9380882-4173709" + \
                         "?openid.assoc_handle=usflex" + \
                         "&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select" + \
                         "&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select" + \
                         "&openid.mode=checkid_setup" + \
                         "&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0" + \
                         "&openid.return_to" + \
                         "=https%3A%2F%2Fwww.amazon.com%2Fgp%2Fyourstore%2Fhome%3Fie%3DUTF8%26ref_%3Dgno_signin"

        try:
            response = self.opener.open(url_login_page)
        except urllib2.HTTPError, e:
            print e.code
            print e.read()
            exit(1)
            return None

        response_text = response.read()
        pattern = '<input(.*?)name="(.+?)"(.*?)value="(.+?)"(.*?)/>'
        matches = re.findall(pattern, response_text)
        params = dict()

        for value in matches:
            if value[1] != 'email' and value[1] != 'create':
                params[value[1]] = value[3]
        params['email'] = self.email
        params['password'] = self.password

        params = urllib.urlencode(params)

        # Post login details ##################################################
        url_login_post = "https://www.amazon.com/ap/signin"

        try:
            response = self.opener.open(url_login_post, params)
        except urllib2.HTTPError, e:
            print e.code
            print e.read()
            exit(1)

        if response.geturl() == "https://www.amazon.com/gp/yourstore/home?ie=UTF8&ref_=gno_signin&":
            print "Log-in for " + self.email + " successful."
        else:
            # response.geturl() == "https://www.amazon.com/ap/signin"
            print "Log-in for " + self.email + " unsuccessful."
            print "Double check your password in ebook.ini."
            print "quitting."
            exit(1)

    def load_config(self):
        """Loads config from file"""
        config_file = os.path.splitext(__file__)[0] + ".ini"

        config = ConfigParser.SafeConfigParser(allow_no_value=True)
        config.optionxform = str
        config.read(config_file)

        self.max_price = config.getfloat("CONFIG", "max_price")
        self.login = config.getboolean("CONFIG", "login")
        if self.login:
            self.email = config.get("CONFIG", "email")
            self.password = config.get("CONFIG", "password")

        self.use_proxy = config.getboolean("CONFIG", "use_proxy")
        if self.use_proxy:
            self.proxy = config.get("CONFIG", "proxy")

        self.authors = config.options("AUTHORS")
        self.ignore = config.options("IGNORE")
        self.own = config.options("OWN")
        self.overwrite = dict(config.items("OVERWRITE"))
        self.books = dict(config.items("BOOKS"))

if __name__ == "__main__":
    EbookSpecials()
