import datetime
import re
import time

import bs4
import requests

from .canteen import (FISH, MEAT, VEGAN, VEGGIE, get_current_week,
                              get_next_week, get_useragent)

DATE_FORMAT_API = '%Y-%m-%d'
CANTEENS = {
    147: {"name": "Mensa HU Nord", "command": "hu_nord"},
    191: {"name": "Mensa HU Oase Adlershof", "command": "hu_adlershof"},
    270: {"name": "Backshop HU Spandauer Straße", "command": "hu_spandauer"},
    271: {"name": "Mensa FU Herrenhaus Düppel", "command": "fu_dueppel"},
    277: {"name": "Backshop FU Rechtswissenschaften", "command": "fu_rechtswissenschaft"},
    319: {"name": "Mensa HTW Wilhelminenhof", "command": "htw_wilhelminenhof"},
    320: {"name": "Mensa HTW Treskowallee", "command": "htw_treskowallee"},
    321: {"name": "Mensa TU Hardenbergstraße", "command": "tu_mensa"},
    322: {"name": "Mensa FU II", "command": "fu_2"},
    323: {"name": "Mensa FU I", "command": "fu_1"},
    367: {"name": "Mensa HU Süd", "command": "hu_sued"},
    368: {"name": "Backshop FU OSI", "command": "fu_osi"},
    526: {"name": "Mensa HWR Badensche Straße", "command": "hwr_badenschestr"},
    527: {"name": "Mensa Berliner Hochschule für Technik Luxemburger Straße", "command": "bht_luxembugerstr"},
    528: {"name": "Mensa FU Lankwitz Malteserstraße", "command": "fu_lankwitz"},
    529: {"name": "Mensa EHB Teltower Damm", "command": "ehb_teltower_damm"},
    530: {"name": "Mensa KHS Weißensee", "command": "khs_weissensee"},
    5302: {"name": "Backshop TU Hardenbergstraße", "command": "tu_mensa_backshop"},
    531: {"name": "Mensa HfM Charlottenstraße", "command": "hfm_charlottenstr"},
    532: {"name": "Backshop KHSB", "command": "khs_backshop"},
    533: {"name": "Mensa HfS Ernst Busch", "command": "hfs_ernstbusch"},
    534: {"name": "Mensa ASH Berlin Hellersdorf", "command": "ash_hellersdorf"},
    537: {"name": "Mensa Charité Zahnklinik", "command": "charite_zahnklinik"},
    538: {"name": "Mensa TU Marchstraße", "command": "tu_marchstr"},
    540: {"name": "Mensa Pastaria TU Architektur", "command": "tu_architektur"},
    541: {"name": "Backshop TU Wetterleuchten", "command": "tu_wetterleuchten"},
    542: {"name": "Mensa FU Pharmazie", "command": "fu_pharmazie"},
    5477: {"name": "Backshop BHT Luxemburger Straße", "command": "bht_luxemburgerstr_backshop"},
    5501: {"name": "Backshop HfM Charlottenstraße", "command": "hfm_charlottenstr_backshop"},
    631: {"name": "Mensa Pasteria TU Veggie 2.0 – Die vegane Mensa", "command": "tu_veggie"},
    657: {"name": "Mensa TU „Skyline“", "command": "tu_skyline"},
    660: {"name": "Mensa FU Koserstraße", "command": "fu_koserstr"},
    661: {"name": "Backshop HU „c.t.“", "command": "hu_ct"},
    723: {"name": "Backshop HfM Neuer Marstall", "command": "hfm_neuer_marstall"},
    727: {"name": "Backshop HWR Alt-Friedrichsfelde", "command": "hwr_alt_friedrichsfelde"},
}


def download_menu(canteen_id, date):
    url = 'https://www.stw.berlin/xhr/speiseplan-wochentag.html'
    params = {'resources_id': canteen_id, 'date': date}
    headers = {'user-agent': get_useragent()}
    request = requests.post(url, data=params, headers=headers)
    request.raise_for_status()
    return request.text


def download_notes(canteen_id):
    url = 'https://www.stw.berlin/xhr/hinweise.html'
    params = {'resources_id': canteen_id, 'date': datetime.date.today().strftime(DATE_FORMAT_API)}
    headers = {'user-agent': get_useragent()}
    request = requests.post(url, data=params, headers=headers)
    request.raise_for_status()
    return request.text


def download_business_hours(canteen_id):
    url = 'https://www.stw.berlin/xhr/speiseplan-und-standortdaten.html'
    params = {'resources_id': canteen_id, 'date': datetime.date.today().strftime(DATE_FORMAT_API)}
    headers = {'user-agent': get_useragent()}
    request = requests.post(url, data=params, headers=headers)
    request.raise_for_status()
    return request.text


def parse_menu(menu_html):
    text = ''
    soup = bs4.BeautifulSoup(menu_html, 'html.parser')
    menu_groups = soup.find_all('div', class_='splGroupWrapper')
    linebreak = ''
    for group in menu_groups:
        group_lines = []
        menu_items = group.find_all('div', class_='splMeal')
        for item in menu_items:
            veggie = item.find_all('img', class_='splIcon')
            annotation = None
            for icon in veggie:
                if 'icons/15.png' in icon.attrs['src']:
                    annotation = VEGAN
                elif 'icons/1.png' in icon.attrs['src']:
                    annotation = VEGGIE
                elif 'icons/38.png' in icon.attrs['src']:
                    annotation = FISH
            if annotation is None:
                annotation = MEAT
            title = item.find('span', class_='bold').text.strip()
            price = item.find('div', class_='text-right').text.strip()
            price_exp = re.compile(r'€ (\d,\d+/\d,\d+).*$')
            price = price_exp.sub('<strong>\g<1>€</strong>', price)
            if price == "":
                price = '<strong>0,00/0,00€</strong>'
            group_lines.append('%s %s: %s' % (annotation, title, price))

        if len(group_lines) > 0:
            group_heading = group.find('div').find('div').text.strip()
            group_text = '<br>'.join(sorted(group_lines)).strip()
            text += '%s <strong>%s</strong><br/>%s' % (linebreak, group_heading, group_text)
            linebreak = '<br/><br/>'
    return text.strip()


def parse_notes(notes_html):
    soup = bs4.BeautifulSoup(notes_html, 'html.parser')
    bookmarking_note = soup.find('article', {'data-hid': '6046-1'})
    if bookmarking_note:
        bookmarking_note.decompose()
    popup_note = soup.find(text=re.compile('Diese Anzeige wird'))
    if popup_note:
        popup_note.parent.decompose()
    duplicate_notes = soup.findAll('div', class_='visible-xs-block')
    for n in duplicate_notes:
        n.decompose()
    notes = soup.get_text().strip()
    if notes == '':
        return ''
    else:
        return '*Hinweise*\n%s' % notes


def parse_business_hours(business_hours_html):
    business_hours = ''
    soup = bs4.BeautifulSoup(business_hours_html, 'html.parser')
    time_icon = soup.find(class_='glyphicon-time')
    transfer_icon = soup.find(class_='glyphicon-transfer')
    education_icon = soup.find(class_='glyphicon-education')

    if time_icon:
        business_hours += '\n*Öffnungszeiten*'
        for sib in time_icon.parent.parent.next_siblings:
            if type(sib) == bs4.Tag and transfer_icon not in sib.descendants and education_icon not in sib.descendants:
                for item in sib.find_all('div', class_='col-xs-10'):
                    for string in item.stripped_strings:
                        business_hours += '\n%s' % string
    return business_hours.strip()


def get_full_text(canteen_id, canteen_business_hours, canteen_notes, date=None):
    day = date or datetime.date.today()
    date_api = day.strftime(DATE_FORMAT_API)
    date_human = day.strftime('%d.%m.%Y')

    menu_html = download_menu(canteen_id, date_api)
    menu = parse_menu(menu_html)

    result = '*%s* (%s)\n\n%s\n\n%s\n\n%s' % (CANTEENS[canteen_id]['name'], date_human, menu, canteen_business_hours,
                                              canteen_notes)
    return re.sub(r'\n\s*\n', '\n\n', result)


def get_date_range():
    return get_current_week() + get_next_week()