# coding: utf-8
import json
import os
from xml.sax.saxutils import escape
from nhentai.constant import LANGUAGE_ISO


def serialize_json(doujinshi, output_dir):
    metadata = {'title': doujinshi.name,
                'subtitle': doujinshi.info.subtitle}
    if doujinshi.info.date:
        metadata['upload_date'] = doujinshi.info.date
    if doujinshi.info.parodies:
        metadata['parody'] = [i.strip() for i in doujinshi.info.parodies.split(',')]
    if doujinshi.info.characters:
        metadata['character'] = [i.strip() for i in doujinshi.info.characters.split(',')]
    if doujinshi.info.tags:
        metadata['tag'] = [i.strip() for i in doujinshi.info.tags.split(',')]
    if doujinshi.info.artists:
        metadata['artist'] = [i.strip() for i in doujinshi.info.artists.split(',')]
    if doujinshi.info.groups:
        metadata['group'] = [i.strip() for i in doujinshi.info.groups.split(',')]
    if doujinshi.info.languages:
        metadata['language'] = [i.strip() for i in doujinshi.info.languages.split(',')]
    metadata['category'] = doujinshi.info.categories
    metadata['URL'] = doujinshi.url
    metadata['Pages'] = doujinshi.pages

    with open(os.path.join(output_dir, 'metadata.json'), 'w') as f:
        json.dump(metadata, f, separators=(',', ':'))


def serialize_comic_xml(doujinshi, output_dir):
    from iso8601 import parse_date
    with open(os.path.join(output_dir, 'ComicInfo.xml'), 'w', encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>\n')
        f.write('<ComicInfo xmlns:xsd="http://www.w3.org/2001/XMLSchema" '
                'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n')
        
        # https://anansi-project.github.io/docs/comicinfo/schemas/v2.1
        xml_write_simple_tag(f, 'Title', doujinshi.pretty_name)
        series = doujinshi.parseseries(doujinshi.pretty_name)
        xml_write_simple_tag(f, 'Series', series if series is not None else doujinshi.pretty_name)

        # Number
        # Count
        # Volume
        # AlternateSeries
        # AlternateNumber
        # AlternateCount

        if doujinshi.pretty_localized_name:
            localized_name = doujinshi.parseseries(doujinshi.pretty_localized_name)
            xml_write_simple_tag(f, 'Summary', localized_name if localized_name is not None else doujinshi.pretty_localized_name)

        # Notes
            
        if doujinshi.info.date:
            dt = parse_date(doujinshi.info.date)
            xml_write_simple_tag(f, 'Year', dt.year)
            xml_write_simple_tag(f, 'Month', dt.month)
            xml_write_simple_tag(f, 'Day', dt.day)
        if doujinshi.artists:
            xml_write_simple_tag(f, 'Writer', ', '.join([i.strip().title() for i in
                doujinshi.artists.split(',')]))

        # Penciller
        # Inker
        # Colorist
        # Letterer
        # CoverArtist
        # Editor 
        # Translator
        
        if doujinshi.groups:
            xml_write_simple_tag(f, 'Publisher', ', '.join([i.strip().title() for i in
                doujinshi.groups.split(',')]))
            
        # Imprint
            
        xml_write_simple_tag(f, 'Genre', doujinshi.info.categories)
        if doujinshi.tags:
            xml_write_simple_tag(f, 'Tags', doujinshi.tags)
        xml_write_simple_tag(f, 'Web', doujinshi.url)
        xml_write_simple_tag(f, 'PageCount', doujinshi.pages)
        if doujinshi.info.languages:
            languages = [i.strip() for i in doujinshi.info.languages.split(',')]
            xml_write_simple_tag(f, 'Translated', 'Yes' if 'translated' in languages else 'No')
            [xml_write_simple_tag(f, 'LanguageISO', LANGUAGE_ISO[i]) for i in languages
             if (i != 'translated' and i in LANGUAGE_ISO)]
        xml_write_simple_tag(f, 'Format', 'Digital')
        xml_write_simple_tag(f, 'BlackAndWhite', 'No' if doujinshi.tags and
            'full color' in doujinshi.tags else 'Yes')
        xml_write_simple_tag(f, 'Manga', 'Yes')
        if doujinshi.characters:
            xml_write_simple_tag(f, 'Characters', ", ".join([i.strip().title() for i in doujinshi.characters.split(',')]))
        if doujinshi.groups:
            xml_write_simple_tag(f, 'Teams', ', '.join([i.strip().title() for i in
                doujinshi.groups.split(',')]))
            
        # Locations
        # ScanInformation
        # StoryArc
        # StoryArcNumber

        if doujinshi.parodies:
            xml_write_simple_tag(f, 'SeriesGroup', doujinshi.parodies.title())
        xml_write_simple_tag(f, 'AgeRating', 'R18+')

        # Pages
        # CommunityRating
        # MainCharacterOrTeam
        # Review
        # GTIN

        # Kavita Specific
        # I would use this if it wasn't broken currently
        #
        # LocalizedSeries

        # Custom
        xml_write_simple_tag(f, 'NhentaiId', doujinshi.id)

        f.write('</ComicInfo>')


def xml_write_simple_tag(f, name, val, indent=1):
    f.write(f'{" "*indent}<{name}>{escape(str(val))}</{name}>\n')


def merge_json():
    lst = []
    output_dir = "./"
    os.chdir(output_dir)
    doujinshi_dirs = next(os.walk('.'))[1]
    for folder in doujinshi_dirs:
        files = os.listdir(folder)
        if 'metadata.json' not in files:
            continue
        data_folder = output_dir + folder + '/' + 'metadata.json'
        json_file = open(data_folder, 'r')
        json_dict = json.load(json_file)
        json_dict['Folder'] = folder
        lst.append(json_dict)
    return lst


def serialize_unique(lst):
    dictionary = {}
    parody = []
    character = []
    tag = []
    artist = []
    group = []
    for dic in lst:
        if 'parody' in dic:
            parody.extend([i for i in dic['parody']])
        if 'character' in dic:
            character.extend([i for i in dic['character']])
        if 'tag' in dic:
            tag.extend([i for i in dic['tag']])
        if 'artist' in dic:
            artist.extend([i for i in dic['artist']])
        if 'group' in dic:
            group.extend([i for i in dic['group']])
    dictionary['parody'] = list(set(parody))
    dictionary['character'] = list(set(character))
    dictionary['tag'] = list(set(tag))
    dictionary['artist'] = list(set(artist))
    dictionary['group'] = list(set(group))
    return dictionary


def set_js_database():
    with open('data.js', 'w') as f:
        indexed_json = merge_json()
        unique_json = json.dumps(serialize_unique(indexed_json), separators=(',', ':'))
        indexed_json = json.dumps(indexed_json, separators=(',', ':'))
        f.write('var data = ' + indexed_json)
        f.write(';\nvar tags = ' + unique_json)
