import re
import pandas as pd
from countryinfo import countries
import requests
from urllib.parse import quote
from branca.element import MacroElement
from jinja2 import Template

country_re = re.compile(r'''^[A-Za-z ]+$''')
respondents_re = re.compile(r'''^GROUP OF ([0-9]*) RESPONDENTS$''')
result_re = re.compile(r'''^(?P<name>[A-Za-z]+) (?P<value>[0-9]+)$''')


def _find_capital(country_name):
    for country in countries:
        if country['name'] == country_name:
            return country['capital']
    print(f'country not found - {country_name}')
    return None


def _find_population(country_name):
    for country in countries:
        if country['name'] == country_name:
            return country['population']
    print(f'country not found - {country_name}')
    return None


def _fetch_coordinates(country_name, city_name):
    if city_name is not None:
        url = f'https://nominatim.openstreetmap.org/search.php?city={quote(city_name)}&country={quote(country_name)}&format=json'
    else:
        url = f'https://nominatim.openstreetmap.org/search.php?country={quote(country_name)}&format=json'
    print(url)
    buf = requests.get(url)
    return buf.json()


def _get_coordinates(country_name, city_name):
    print(f"coordinates for {country_name}->{city_name}")
    if city_name:
        response = _fetch_coordinates(country_name, city_name)
        if len(response) == 0:
            print("city not located")
            response = _fetch_coordinates(country_name, None)
            if len(response) == 0:
                print("nor country located")
    else:
        print("no city, so locating country")
        quoted = quote(country_name)
        response = _fetch_coordinates(country_name, None)
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
                    city = _find_capital(country)
                    if city is None:
                        print("!! processing for country")
                        coordinates = _get_coordinates(country, None)
                    else:
                        print("processing for city")
                        coordinates = _get_coordinates(country, city)
                    population = _find_population(country)
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
                respondents = found[0]
                # print(respondents)
                row['respondents'] = int(respondents)
                continue
            found = result_re.findall(l)
            if found:
                # print(found)
                row[found[0][0]] = int(found[0][1])
    if row:
        d.append(row)

    df = pd.DataFrame(d)
    df.to_excel(to_name)


def legend(folium_map, sections):
    """takes two parameters - folium map, and list of section for legend """

    legend_html = '''
    {% macro html(this, kwargs) %}
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>jQuery UI Draggable - Default functionality</title>
      <link rel="stylesheet" href="//code.jquery.com/ui/1.12.1/themes/base/jquery-ui.css">
    
      <script src="https://code.jquery.com/jquery-1.12.4.js"></script>
      <script src="https://code.jquery.com/ui/1.12.1/jquery-ui.js"></script>
      
      <script>
      $( function() {
        $( "#maplegend" ).draggable({
                        start: function (event, ui) {
                            $(this).css({
                                right: "auto",
                                top: "auto",
                                bottom: "auto"
                            });
                        }
                    });
    });
    
      </script>
    </head>
    <body> 
      <div id='maplegend' class='maplegend' 
         style='position: absolute; z-index:9999; border:2px solid grey; background-color:rgba(255, 255, 255, 0.8);
         border-radius:6px; padding: 10px; font-size:14px; left: 20px; bottom: 20px;'>
         
        <div class='legend-title'>Legend (draggable!)</div>
          <div class='legend-scale'>
            <ul class='legend-labels'>
            {% for s in this.sections -%}
              <li><span style='background:{{ s.fill_color }};opacity:0.7;'></span>{{ s.description }}</li>
            {% endfor %}
            </ul>
          </div>
        </div>
      </div>
    </body>
    </html>
    
    <style type='text/css'>
      .maplegend .legend-title {
        text-align: left;
        margin-bottom: 5px;
        font-weight: bold;
        font-size: 90%;
        }
      .maplegend .legend-scale ul {
        margin: 0;
        margin-bottom: 5px;
        padding: 0;
        float: left;
        list-style: none;
        }
      .maplegend .legend-scale ul li {
        font-size: 80%;
        list-style: none;
        margin-left: 0;
        line-height: 18px;
        margin-bottom: 2px;
        }
      .maplegend ul.legend-labels li span {
        display: block;
        float: left;
        height: 16px;
        width: 30px;
        margin-right: 5px;
        margin-left: 0;
        border: 1px solid #999;
        }
      .maplegend .legend-source {
        font-size: 80%;
        color: #777;
        clear: both;
        }
      .maplegend a {
        color: #777;
        }
    </style>
    {% endmacro %}
    '''
    macro = MacroElement()
    macro._template = Template(legend_html)
    macro.sections = sections

    folium_map.get_root().add_child(macro)
