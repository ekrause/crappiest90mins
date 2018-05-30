#!/usr/bin/env python3
"""GET WEIRD"""

# By Vernon Jones

import re
from typing import Optional, List, Iterator, Tuple
import urllib3

from bs4 import BeautifulSoup
import requests


class WeirdWednesdayLookupError(ValueError):
    """yep"""
    pass


def main():
    """main function"""
    try:
        (name, imdb) = whats_weird_this_week()
    except WeirdWednesdayLookupError as yep:
        print(yep)
        return
    print(f"Best guess for movie name: {name}")
    if imdb:
        print(f"IMDB url: {imdb}")
    else:
        print("no matches found on IMDB")


def whats_weird_this_week() -> Tuple[str, Optional[str]]:
    """
    Scrapes the Joy Cinema site to determine what movie is playing for
    weird wednesday this week.
    Returns a tuple of (MOVIE_NAME, IMDB_URL) if it could be detected,
    raises WeirdWednesdayLookupError if the movie couldn't be detected.
    """
    image_uri = get_weird_wednesday_image()
    best_guess = reverse_image_search(image_uri)
    if best_guess == "question mark background gif":
        raise WeirdWednesdayLookupError("No details posted yet! Check back later")
    imdb_urls = search_movie_uri_on_imdb(best_guess)
    best_imdb_match = next(imdb_urls, None)
    return (best_guess, best_imdb_match)


def get_weird_wednesday_image() -> str:
    """returns the url to the weird wednesday poster"""
    joy_cinema = "http://www.thejoycinema.com/index.html"
    text: str = requests.get(joy_cinema).text
    # TODO use beautiful soup for god's sake. You're not an animal!
    weird_wednesday = re.search(r"(?i)weird\s*wednesday", text)
    pos: int = weird_wednesday.end()
    interesting_text: List[str] = text[pos:].splitlines()
    images: List[str] = [x for x in interesting_text if "<img" in x]
    ww_image_raw = images[0]
    src = re.findall(r'''img src="([^"]+)"''', ww_image_raw)
    parsed = urllib3.util.parse_url(joy_cinema)
    start_path = f"{parsed.scheme}://{parsed.host}"
    # lol this is probably a hack
    image_uri = src[0]
    full_image_uri = f"{start_path}{image_uri}"
    return full_image_uri


def reverse_image_search(image_uri: str) -> str:
    """
    Queries google's reverse image search to identify
    the image located at `image_uri`. Returns whatever
    google says is the "Best Guess".
    """
    google_search = f"https://images.google.com/searchbyimage?image_url={image_uri}"
    user_agent = "Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0"
    headers = {"User-Agent": user_agent}
    text: str = requests.get(google_search, headers=headers).text
    # TODO use beautiful soup for god's sake. You're not an animal!
    found = text.find("Best guess for this image:")
    found_text = text[found:].splitlines()[0]
    found = re.finditer(r">[^<]+", found_text)
    return next(found).group(0)[1:]


def search_movie_uri_on_imdb(title: str) -> Iterator[str]:
    """returns the URL to a movie on IMDB based on its title"""
    stringified = '+'.join(title.split())
    uri = f"https://www.imdb.com/find?ref_=nv_sr_fn&q={stringified}&s=tt"
    text: str = requests.get(uri).text
    soup = BeautifulSoup(text, 'html.parser')
    find_section = [x for x in soup.find_all("div") if 'findSection' in x.get('class', [])]
    if not find_section:
        yield from []
        return
    assert len(find_section) == 1, "Expected the find section to only have one result"
    (table,) = find_section
    matches = (x for x in table.find_all("tr"))
    for each in matches:
        href = each.find_all("a")[0].get('href')
        yield "https://www.imdb.com" + href


if __name__ == '__main__':
    main()
