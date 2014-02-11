#!/usr/bin/python

"""Amazon e-book Specials checker
This program checks for books by <authors> (using their amazon ID) which cost less than <price> and filters out all books in <ignore>
You can also overwrite <price> for a specific book by adding its name and value to the <overwrite> dictionary
"""

import urllib2, unicodedata
from bs4 import BeautifulSoup

minprice = 4.99

authors = {
  "mclellan":"B009IA053A",
  "kay":"B000AQ6VIO",
  "hearne":"B004FR1V8O",
  "pratchett":"B000AQ0NN8",
  "lukyanenko":"B0036ER41K",
  "sanderson":"B001IGFHW6",
  "parker":"B001ILKHK8",
  "lynch ":"B001DABSBQ",
  "butcher":"B001H6U718",
  "jordan":"B000AQ19X6",
  "card":"B000AQ3SS0",
  "rothfuss":"B001DAHXZQ",
  "hobb":"B000AP7LIY",
  "canavan":"B001IODIG0",
  "abercrombie":"B001JP7WJC",
  "sullivan":"B002BOJ41O",
  "goodkind":"B000APZOQA",
  "adams":"B000AQ2A84",
  "tolkien":"B000ARC6KA"
  #"london":"B000AP1TJQ"
  }

ignore = [
  "B00ARJP2UM", "B0040ZN3M8", "B00F2SZ7YO", "B005SFRJ6K", "B0071NMDZ4", "B00DTUHIKS",
  "B008D272PI", "B00AZR6GWO", "B009R682L2", "B00DQ8L0UC", "B009AEM4NI", "B0082CBV5G",
  "B00FYKWWG6", "B002PA0LW0", "B005FWPMOM", "B0081V4PQ0", "B00ARKCRR2", "B00AWR01N2",
  "B00AWR01SM", "B00AAJQZ3C", "B00AAJQZ6E", "B00AAJR3F6", "B000FCKCWO", "B000UZNQNS",
  #Maybe later:
  "B00BBA6FJ8","B003H4I5LC","B003GY0KUM","B008GT83FG","B000NJL79G","B00B72CFN0",
  ]

own = [
  "B004J4WN0I", "B00AUSCOIS", "B008TSC2E2",  #Hearne
  "B005FFW46S", "B00BW2MOKO", "B006O41HTO", "B000W965QM", "B000UVBT7M", "B000UVBT3G", "B000W912Q0", "B000W916WK", # Pratchett
  "B003V4B4GQ", "B003P2WO5E", "B00ARHAAZ6", #Sanderson
  "B002VBV1R2", "B00329UWL8", "B00BMKDTNC", #Jordan
  "B00433TO4I", "B004DNW65W", #Goodkind
  "B003G4W49C", "B003GY0KUW", "B003GWX8SK", #Card
  "B000JMKNJ2", #Lynch
  "B0092XHPIG", #McClellan
  "B005QOIHR8", #Sullivan
  "B00338QEUG", "B005LC1N6M", "B003H4I5SU", "B0089LOD6Y", "B000FC0XV4", #Hobb
  "B00B3VX3QS", #Parker
  "B00480O978", #Abercrombie 
  "B003YL4LYI", #Martin
  "B0090UOJAI", #Butcher
  "B00DB3FSNW", "B00DB3FSQY", #Lukyanenko
  "B000N2HCWY", #Canavan
  "B00AVNAWSG",  #Compilation
  ]

overwrite = {
  "B00FE02TAU":0.99, "B00DP7OXOE":0.99, "B00HZ6780W":2.99, #McClellan
  "B0099D4KEG":2.99, "B004H1TQBW":8, #Sanderson
  "B00C8S9UXA":2.99, "B00I1LS0SE":0.99, #Hearne
  "B00413QA9C":4.50, #Card
  }

# Book url = "http://www.amazon.com/gp/product/" + bookID
books = {
  #"B00DB3FSQY":-1, # Day Watch Watch by Sergei Lukyanenko
  "B00CYNGPTG":-1, # Dust by Hugh Howey
  "B000UOJTRQ":-1, # The Praxis by Walter Jon Williams
  "B005IHW7MO":-1, # Bagombo Snuff Box: Uncollected Short Fiction by Kurt Vonnegut 
  "B0052RERW8":-1, # Prince of Thorns by Mark Lawrence
  "B00FIN0TGY":11.84, # Raising Steam by Terry Pratchett
  "B00FJ3A48G":11.84, # The Long Mars by Terry Pratchett
  "B004J4WLIM":10.99, # The Republic of Thieves by Scott Lynch
  "B00DA6YEKS":11.24, # Words of Radiance by Brandon Sanderson
  "B001NXK1XO":9.99, # The Drunkard's Walk: How Randomness Rules Our Lives by Leonard Mlodinow
  "B00HL0MA3W":40, # The Malazan Empire by Steven Erikson
  }

def main(minprice, authors = {}, ignore = [], own = [], overwrite = {}, books = {}):
  """Go through whole list of authors and call <getPage()> for each author and result page"""
  message = unicode('')
  for authorID in authors.values():
      result = checkPage(authorID, minprice, ignore, own, overwrite) #run once to get first page and a page count
      if result:
        m, pages, more = result
        message += unicode(m)
        for page in range(2,pages+1): #run for the other pages if there is more than one
            if more == True:
                m, more = checkPage(authorID, minprice, ignore, own, overwrite, page)
                message += unicode(m)
      else:
        print "Could not connect"
        return   
      
  for bookID in books.keys():
    minBookPrice = minprice if books[bookID] < 0 else books[bookID]
    m = checkBook(bookID,minBookPrice)
    message += unicode(m)

  message = unicodedata.normalize('NFKD', message).encode('ascii','ignore')  
  if message == '':
      message = "No books cheaper than $" + str(minprice)
  message = "======e-books cheaper than $"  + str(minprice) + "======\n" + message
  print message

def checkPage(authorID, minprice, ignore, own, overwrite, page=1):
    """
    Checks one page for specials and returns the found specials,
    the number of pages and if you should look for more specials.
    """
    
    url = "http://www.amazon.com/r/e/" + authorID + "/?rh=n%3A283155%2Cp_n_feature_browse-bin%3A618073011&sort=price&page=" + str(page);
                
    try:
        data = str(urllib2.urlopen(url).read())
    except:
        return None 

    soup = BeautifulSoup(data, "html5lib")
    
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
        if dprice < minprice:
          if bookID in ignore or bookID in own:
            continue
          elif bookID in overwrite:
            if dprice < overwrite[bookID]:
              message += name + " " + price + " - " + link + "\n"
          else:
            message += name + " " + price + " - " + link + "\n"
        else:
            more = False
    
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
    
def checkBook(bookID,min_price):
  """Check price of specific book"""
  url = "http://www.amazon.com/gp/product/" + bookID
  try:
    data = str(urllib2.urlopen(url).read())
  except:
    return None

  soup = BeautifulSoup(data, "html5lib")
  name = soup.title.string[12:-14]
  price = soup("div", "buying", id="priceBlock")[0](True,'priceLarge')[0].string.strip()
  dprice = float(price[1:])
  message = ""
  if dprice < min_price:
    message = name + " " + price + " - " + url + "\n"
  return message

if __name__ == "__main__":
  main(minprice, authors, ignore, own, overwrite, books)
