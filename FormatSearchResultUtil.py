import string
from requests_html import HTMLSession
from html2text import HTML2Text
import re


def removeUnwantedChars(formatted_search_result):
    x = formatted_search_result.translate (str.maketrans('', '', string.punctuation))
    x = x.replace('-', '')
    x = re.sub(r'[^a-zA-Z\'] ]+', "", x).lower()
    return x


def getSearchResultBody(url):
    session = HTMLSession()
    convertHTMLToText = HTML2Text()
    convertHTMLToText.ignore_links = True
    
    response = session.get(url)
    try:
        result = response.html.find('body', first=True)
    except:
        result = ""
    
    if not result:
        return ''
    return convertHTMLToText.handle(result.html)
