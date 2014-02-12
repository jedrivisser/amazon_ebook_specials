#!/usr/bin/python

import urllib, urllib2, unicodedata, cookielib, re, ConfigParser
from bs4 import BeautifulSoup

class EbookSpecials:
  """Amazon e-book Specials checker

  This program checks for books by <authors> (using their amazon ID) which cost less than <price> and filters out all books in <ignore> 
  You can also overwrite <price> for a specific book by adding its name and value to the <overwrite> dictionary
  
  """

  def __init__(self):
    ########### Set up opener and cookies ############
    cj = cookielib.CookieJar()
    self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    self.opener.addheaders = [('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:26.0) Gecko/20100101 Firefox/26.0'),]
 
    self.loadConfig()

    if self.login:
      self.doLogin()
 
    ### Go through whole list of authors and call getPage() for each result page for each author ###
    message = unicode('')
    for authorID in self.authors.values():
        result = self.checkPage(authorID) #run once to get first page and a page count
        if result:
          m, pages, more = result
          message += unicode(m)
          for page in range(2,pages+1): #run for the other pages if there is more than one
              if more == True:
                  m, more = self.checkPage(authorID, page)
                  message += unicode(m)
        else:
          print "Could not connect"
          return   
        
    for bookID in self.books.keys():
      minBookPrice = self.minprice if float(self.books[bookID]) < 0 else float(self.books[bookID])
      m = self.checkBook(bookID,minBookPrice)
      message += unicode(m)
  
    message = unicodedata.normalize('NFKD', message).encode('ascii','ignore')  
    if message == '':
        message = "No books cheaper than $" + str(self.minprice)
    message = "======e-books cheaper than $"  + str(self.minprice) + "======\n" + message
    print message
  
  def checkPage(self, authorID, page=1):
      """
      Checks one page for specials and returns the found specials,
      the number of pages, and if you should look for more specials.
      
      """
      
      url = "http://www.amazon.com/r/e/" + authorID + "/?rh=n%3A283155%2Cp_n_feature_browse-bin%3A618073011&sort=price&page=" + str(page);
                  
      try:
          data = str(self.opener.open(url).read())
      except:
          return None 
  
      #soup = BeautifulSoup(data, "html5lib")
      soup = BeautifulSoup(data, "html.parser")
      
      books = soup("div", "list results twister")[0].select('div.result.product.celwidget')
      message = ""
      more = True
      for book in books:
          bookID = book['name']
          name = book('h3')[0]('a')[0].string
          link = book('h3')[0]('a')[0]['href']
          if not link.startswith("http://www.amazon.com"):
          	link = "http://www.amazon.com" + link
          price = book('div','tp')[0]('table')[0]('tr')[1]('td')[2]('a')[0].string
          dprice = float(price[1:])
          if dprice < self.minprice:
            if bookID in self.ignore or bookID in self.own:
              continue
            elif bookID in self.overwrite:
              if dprice < float(self.overwrite[bookID]):
                message += name + " " + price + " - " + link + "\n"
            else:
              message += name + " " + price + " - " + link + "\n"
          else:
              more = False #set more to false is prices on page go above 'minprice'
      
      if page==1:
          if soup('span', "pagnDisabled"):
              pages = int(soup('span', "pagnDisabled")[0].string)
          elif soup('span', "pagnLink"):
              pages = int(soup('span', "pagnLink")[-1].string)
          else:
              pages = 1
          return message, pages, more
      else:
          return message, more
      
  def checkBook(self, bookID, min_price):
    """Check price of specific book from the [BOOKS] section"""

    url = "http://www.amazon.com/gp/product/" + bookID
    try:
      data = str(self.opener.open(url).read())
    except:
      return None

    #soup = BeautifulSoup(data, "html5lib")
    soup = BeautifulSoup(data, "html.parser")

    #print soup("span", id="btAsinTitle")
    name = soup.title.string[12:-14]
    price = soup("div", "buying", id="priceBlock")[0](True,'priceLarge')[0].string.strip()
    dprice = float(price[1:])
    message = ""
    if dprice < min_price:
      message = name + " " + price + " - " + url + "\n"
    return message
  
  def doLogin(self):
    """Log-in to you amazon account"""
  
    ########################## Get and set form params ############################
    url_login_page = "https://www.amazon.com/ap/signin/182-9380882-4173709?_encoding=UTF8&_encoding=UTF8&openid.assoc_handle=usflex&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.mode=checkid_setup&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0&openid.ns.pape=http%3A%2F%2Fspecs.openid.net%2Fextensions%2Fpape%2F1.0&openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.amazon.com%2Fgp%2Fyourstore%2Fhome%3Fie%3DUTF8%26ref_%3Dgno_signin"
    try:
        response = self.opener.open(url_login_page)
    except urllib2.HTTPError, e:
        print e.code
        print e.read()
        exit(1)
  
    rspTxt = response.read()
    pattern = '<input(.*?)name="(.+?)"(.*?)value="(.+?)"(.*?)/>'
    matches = re.findall(pattern, rspTxt)
    params = dict();
  
    for value in matches:
      if value[1]!='email' and value[1]!='create':
        params[value[1]] = value[3]
    params['email'] = self.email
    params['password'] = self.password
  
    params = urllib.urlencode(params)
  
    ############################# Post login details ##############################
    url_login_post = "https://www.amazon.com/ap/signin"
  
    try:
        response = self.opener.open(url_login_post,params)
    except urllib2.HTTPError, e:
        print e.code
        print e.read()
        exit(1)

    if response.geturl() == "https://www.amazon.com/gp/yourstore/home?ie=UTF8&ref_=gno_signin&":
      print "Log-in for " + self.email + " successful."
    else:
      #response.geturl() == "https://www.amazon.com/ap/signin"
      print "Log-in for " + self.email + " unsuccessful."
      print "Double check your password in ebook.ini."
      print "quitting."
      exit(1)

  def loadConfig(self):
    """Loads config from file"""
    Config = ConfigParser.SafeConfigParser(allow_no_value=True)
    Config.optionxform = str
    Config.read("ebook.ini")
    
    
    self.minprice = float(Config.get("CONFIG", "minprice"))
    self.login = Config.getboolean("CONFIG", "login")
    if self.login:
      self.email = Config.get("CONFIG", "email")
      self.password = Config.get("CONFIG", "password")

    
    self.authors = dict(Config.items("AUTHORS"))
    self.ignore = Config.options("IGNORE")
    self.own = Config.options("OWN")
    self.overwrite = dict(Config.items("OVERWRITE"))
    self.books = dict(Config.items("BOOKS"))

if __name__ == "__main__":
  EbookSpecials()
