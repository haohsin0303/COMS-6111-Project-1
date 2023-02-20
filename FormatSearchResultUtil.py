import re
import string
from html2text import HTML2Text
from requests_html import HTMLSession


def removeUnwantedChars(formatted_search_result):
    """
    Removes the unwanted punctuations in the combined string result
    """

    removed_punct_string = formatted_search_result.translate (str.maketrans('', '', string.punctuation))
    removed_punct_string = removed_punct_string.replace('-', '')
    removed_punct_string = re.sub(r'[^a-zA-Z\'] ]+', "", removed_punct_string).lower()
    return removed_punct_string


def getSearchResultBody(url):
    """
    Performs in-depth search result with the url link to get full body text
    Only used if iteration count exceeds 5+. 
    """

    session = HTMLSession()
    convertHTMLToText = HTML2Text()
    convertHTMLToText.ignore_links = True
    convertHTMLToText.ignore_images = True
    
    response = session.get(url)
    try:
        result = response.html.find('body', first=True)
    except:
        result = ""
    
    if not result:
        return ""
    else:
        return convertHTMLToText.handle(result.html)
