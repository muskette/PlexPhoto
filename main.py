import logging
import os
import re

from urllib import parse as urlparse
from urllib import error as http_error
from uuid import uuid4

import wget
from datetime import datetime

import requests
from lxml import etree
from plexapi.myplex import MyPlexAccount


def get_logger():
    """Return simple console logger"""
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    # add the handlers to log
    log.addHandler(ch)
    return log


log = get_logger()


def parse_xml_from_unicode(unicode_str):
    """
    :param unicode_str: XML formatted string
    :return: lxml Element object
    """
    s = unicode_str.encode('utf-8')
    return etree.fromstring(s, parser=etree.XMLParser(encoding='utf-8'))


def get_plex_server(user, password, servername):
    """
    :param user: username
    :param password: password
    :param servername: plex server name
    :return: API object representing server instance
    """
    log.info("Getting Plex server instance")
    acc = MyPlexAccount(user, password)
    server = acc.resource(servername).connect()
    return server


def get_arts_url(server_base, key, session_token):
    """Arts is an api endpoint for background art of a media item"""
    return f'{server_base}/library/metadata/{key}/arts?X-Plex-Token={session_token}'


def query_xml_endpoint(url):
    response_as_xml = requests.get(url).text
    xml_elem = parse_xml_from_unicode(response_as_xml)
    return xml_elem


def flatten(lol):
    """Flatten a list of lists"""
    return [item for sublist in lol for item in sublist]


def clean_library_urls(urls, server_instance):
    """
    Background images currently selected by the plex server return as relative /library urls.
    All others return as absolute http urls
    This cleans the relative urls into absolute urls
    """
    log.info("Cleaning up photo urls")
    for index, item in enumerate(urls):
        if item.startswith('/library'):
            urls[index] = server_instance._baseurl + item + "&X-Plex-Token={0}".format(server_instance._token)


def media_items(server):
    server = get_plex_server('XXXXXXXXX', 'XXXXXXXXX', 'XXXXXXXXX')
    for library_section in server.library.sections():
        for media_item in library_section.all():
            yield media_item


def get_background_art_urls():
    """
    Retrieves every url for background art in a plex server

    It iterate's the server's libraries
    for each library, it gets the media object
    for each media object, it gets the API endpoint used to retrieve the urls
    for each url, it queries the endpoint and parses the image urls from the XML response
    :return: list of urls
    """
    server = get_plex_server('XXXXXXXXX', 'XXXXXXXXX', 'XXXXXXXXX')

    log.info("Querying server for all media items")
    # all_media_items = [library_section.all() for library_section in server.library.sections()]
    log.info("Parsing media items for background art urls")
    all_arts_urls = [get_arts_url(server._baseurl, x.ratingKey, server._token) for x in media_items(server)]
    log.debug(f"{len(all_arts_urls)} media items.")
    log.info("Querying server for background art urls")
    all_xml_results = [query_xml_endpoint(x) for x in all_arts_urls]
    log.info("Parsing XML response for background art urls")
    all_photo_elements = [tree_item.iter('Photo') for tree_item in all_xml_results]
    all_photo_urls = [x.attrib['key'] for x in flatten(all_photo_elements)]
    clean_library_urls(all_photo_urls, server)
    return all_photo_urls



from timeit import default_timer
class Timer(object):
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.timer = default_timer

    def __enter__(self):
        self.start = self.timer()
        return self

    def __exit__(self, *args):
        end = self.timer()
        self.elapsed_secs = end - self.start
        self.elapsed = self.elapsed_secs # seconds
        log.debug('Elapsed time: {0:.4f} seconds'.format(self.elapsed))


def decode_url(url):
    ret = urlparse.unquote_plus(url)
    while ret != urlparse.unquote_plus(ret):
        # keep unquoting until a stable decoded url is reached
        ret = urlparse.unquote_plus(ret)
    return ret


def create_filename(url):
    """
    We're gonna do some messy stuff to try and extract a filename from the query parameters
    The structure of the url aries wildly based on the plex agent

    A repeatably retrievable string of unique characters for this image is nice to have
    because it will prevent duplicates when running this script a second time.

    Trying for robustness with this nice-to-have feature will hit seriously diminishing returns
    so if anything goes wrong, let's just uuid the filename. We don't expect this to occur too often
    """
    try:
        url = decode_url(url)
        path_regex = r"(url\=[a-z]*\:\/\/)(.*)\&"
        url_substring = re.findall(path_regex, url)[0][1]
        url_substring = url_substring.replace('.', '_')
        url_substring = url_substring.replace('/', '_')
        if url_substring.endswith('_jpg'):
            url_substring = url_substring[:-4]
        if url_substring.endswith('jpg'):
            # ends with jpg but not as an file extension
            url_substring = url_substring[:-3]
        return url_substring + '.jpg'
    except:
        # If we fail while parsing this url, let's just use a random name
        return str(uuid4()) + '.jpg'


if __name__ == '__main__':
    album_loc = f'./{datetime.now().strftime("%Y_%m_%d_%H_%M_%S")}'
    os.makedirs(album_loc)
    image_urls = get_background_art_urls()
    log.info(f"Downloading {len(image_urls)} images")
    count = 0
    for url in image_urls:
        filename = wget.detect_filename(url)
        if filename == 'file':
            filename = create_filename(url)
        try:
            wget.download(url, f"{album_loc}/{filename}")
            count += 1
            log.debug(f"Downloaded {count} files")
        except http_error.HTTPError:
            log.warn("Couldn't retrieve image file, skipping")
            log.debug(f"Failed url: {url}")
    log.info("Finished")
