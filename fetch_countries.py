from countryinfo import countries
import json
from urllib.parse import quote,unquote
import requests
from time import sleep
from bs4 import BeautifulSoup
import re


def recode_countryinfo():
    """some entres are utf-encoded - to clean that you can use this code...
    Result is stored in data.json, so you can copy data to countryinfo.py file"""
    res = []
    for country in countries:
        c = {
            'name': unquote(country['name']),
            'code': country['code'],
            'capital': unquote(country['capital']),
            'continent': country['continent'],
            'timezones': country['timezones']
        }
        res.append(c)

    with open('data.json', 'w', encoding='utf-8') as outfile:
        json.dump(res, outfile, ensure_ascii=False, indent=4)


def read_countries_from_wikipedia():
    """Read pages from wiki, and store locally. Yes Wikipedia is against crowling, but here amount is small, and storing
    data helps limit load at Wikipedia side + sleep added"""
    for country in countries:
        if not country['name'] in ('Macedonia'):
            print("-><- ")
            continue

        if country['name'] == 'Macedonia':
            country_name = quote('North Macedonia')
        else:
            country_name = quote(country['name'])

        url = f"https://en.wikipedia.org/wiki/{country_name}"
        print(f"{country['name']} -> {url}")
        buf = requests.get(url)
        refers_re = re.compile(country['name'] + r".*usually refers to:", re.IGNORECASE)
        if refers_re.search(buf.text):
            # ie for Georgia
            url = f"https://en.wikipedia.org/wiki/{country_name}_(country)"
            print(f"{country['name']} --> {url}")
            buf = requests.get(url)
        if "Wikipedia does not have an article with this exact name" in buf.text:
            raise Exception(f"failed to fetch {country['name']} -> {url}")
        with open(f"wiki-countries/{country['name']}.html", 'w', encoding='utf-8') as outfile:
            outfile.write(buf.text)
        sleep(3)


def load_data_from_wiki_files_to_countryinfo():
    """read stored files, and update countryinfo with population, and other demographic data"""
    for country in countries:
        print(f"{country['name']}")

        # country_name = quote(country['name'])
        # if not country['name'] in ('Macedonia'):
        #     print("-><- ")
        #     continue
        with open(f"wiki-countries/{country['name']}.html", 'r', encoding='utf-8') as infile:
            content = "\n".join(infile.readlines())
        soup = BeautifulSoup(content, 'html.parser')
        population = read_population(soup)
        print(f"population: {population}")
        country['population'] = population

    with open('data.json', 'w', encoding='utf-8') as outfile:
        json.dump(countries, outfile, ensure_ascii=False, indent=4)


def read_population(soup):
    """read population from provided content"""
    result = soup.find('a', string='Population')
    if result is None:
        result = soup.find('th', string='Population')
        if result is None:
            return None
        if result.nextSibling is not None and result.nextSibling.__dict__.get('name', '') == 'td':
            result = result.nextSibling.text
        else:
            result = result.parent.nextSibling
            result = result.find('td').text
    else:
        result = result.parent.parent.nextSibling
        result = result.find('td').text
    num_re = re.compile(r"[0-9 \,]+", re.IGNORECASE)
    match = num_re.search(result)
    if match:
        num = match.group(0)
    else:
        return None
    return int(num.replace(",", ""))
#
#
# def read_gdp(soup):
#     """Read GDP per capita for provided coutry"""
#     result = soup.find('a', string='GDP')
#     if result is None:
#         result = soup.find('th', string='GDP')
#         if result is None:
#             return None
#         if result.nextSibling is not None and result.nextSibling.__dict__.get('name', '') == 'td':
#             result = result.nextSibling.text
#         else:
#             result = result.parent.nextSibling
#             result = result.find('td').text
#     else:
#         result = result.parent.parent.nextSibling
#         result = result.find('td').text
#     num_re = re.compile(r"[0-9 \,]+", re.IGNORECASE)
#     match = num_re.search(result)
#     if match:
#         num = match.group(0)
#     else:
#         return None
#     return int(num.replace(",", ""))


if __name__ == "__main__":
    load_data_from_wiki_files_to_countryinfo()
