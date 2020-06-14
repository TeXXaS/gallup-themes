import re
import pandas as pd
from countryinfo import countries
import requests
from urllib.parse import quote

country_re = re.compile(r'''^[A-Za-z ]+$''')
respondents_re = re.compile(r'''^GROUP OF ([0-9]*) RESPONDENTS$''')
result_re = re.compile(r'''^(?P<name>[A-Za-z]+) (?P<value>[0-9]+)$''')


def find_capital(country_name):
    for country in countries:
        if country['name'] == country_name:
            return country['capital']
    print(f'country not found - {country_name}')
    return None


def find_population(country_name):
    for country in countries:
        if country['name'] == country_name:
            return country['population']
    print(f'country not found - {country_name}')
    return None


def fetch_coordinates(country_name, city_name):
    if city_name is not None:
        url = f'https://nominatim.openstreetmap.org/search.php?city={quote(city_name)}&country={quote(country_name)}&format=json'
    else:
        url = f'https://nominatim.openstreetmap.org/search.php?country={quote(country_name)}&format=json'
    print(url)
    buf = requests.get(url)
    return buf.json()


def get_coordinates(country_name, city_name):
    print(f"coordinates for {country_name}->{city_name}")
    if city_name:
        response = fetch_coordinates(country_name, city_name)
        if len(response) == 0:
            print("city not located")
            response = fetch_coordinates(country_name, None)
            if len(response) == 0:
                print("nor country located")
    else:
        print("no city, so locating country")
        quoted = quote(country_name)
        response = fetch_coordinates(country_name, None)
        if len(response) == 0:
            print("country not located")

    if len(response) == 0:
        return {'lat': None, 'lon': None}

    idx = 0
    while response[idx]['type'] not in ('administrative', 'city') and idx < (len(response) - 1):
        idx += 1
    return {
        'lat': response[idx]['lat'],
        'lon': response[idx]['lon']
    }


def convert_to_excel(from_name, to_name):
    d = []
    with open(from_name, 'r') as f:
        lines = f.readlines()
        row = {}
        for l in lines:
            found = country_re.findall(l)
            if found:
                if row:
                    d.append(row)
                    row = {}
                country = found[0]
                if country == 'Korea':
                    country = 'South Korea'
                if country == 'China and Hong Kong':
                    country = 'China'
                if country == 'US Virgin Islands':
                    country = 'United States Virgin Islands'
                print(country)
                if country not in ['All CSF', 'Females', 'Males']:
                    city = find_capital(country)
                    if city is None:
                        print("!! processing for country")
                        coordinates = get_coordinates(country, None)
                    else:
                        print("processing for city")
                        coordinates = get_coordinates(country, city)
                    population = find_population(country)
                    row = {
                        'country': country,
                        'lat': coordinates['lat'],
                        'lon': coordinates['lon'],
                        'population': population
                    }
                else:
                    row = {
                        'country': country,
                        'lat': None,
                        'lon': None
                    }
                continue
            found = respondents_re.findall(l)
            if found:
                respondants = found[0]
                # print(respondants)
                row['respondants'] = int(respondants)
                continue
            found = result_re.findall(l)
            if found:
                # print(found)
                row[found[0][0]] = int(found[0][1])
    if row:
        d.append(row)

    df = pd.DataFrame(d)
    df.to_excel(to_name)
