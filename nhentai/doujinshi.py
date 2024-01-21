# coding: utf-8

from tabulate import tabulate
import re

from nhentai.constant import DETAIL_URL, IMAGE_URL
from nhentai.logger import logger
from nhentai.utils import format_filename


EXT_MAP = {
    'j': 'jpg',
    'p': 'png',
    'g': 'gif',
}

MANGA_SERIES_REGEX = [
    r"(?P<Series>.+?)Том(а?)(\.?)(\s|_)?(?P<Volume>\d+(?:(\-)\d+)?)",
    r"(?P<Series>.+?)(\s|_)?(?P<Volume>\d+(?:(\-)\d+)?)(\s|_)Том(а?)",
    r"(?P<Series>.+?)(?!Том)(?<!Том\.)\s\d+(\s|_)?(?P<Chapter>\d+(?:\.\d+|-\d+)?)(\s|_)(Глава|глава|Главы|Глава)",
    r"(?P<Series>.+?)(Глава|глава|Главы|Глава)(\.?)(\s|_)?(?P<Chapter>\d+(?:.\d+|-\d+)?)",
    r"(?P<Series>.*)(\b|_|-|\s)(?:sp)\d",
    r"(?P<Series>.+?)(\s|_|-)+(?:Vol(ume|\.)?(\s|_|-)+\d+)(\s|_|-)+(?:(Ch|Chapter|Ch)\.?)(\s|_|-)+(?P<Chapter>\d+)",
    r"^(?P<Series>.+?)(\s*Chapter\s*\d+)?(\s|_|\-\s)+Vol(ume)?\.?(\d+|tbd|\s\d).+?",
    r"(?P<Series>.*)(\b|_)v(?P<Volume>\d+-?\d*)(\s|_|-)",
    r"(?P<Series>.*)( - )(?:v|vo|c|chapters)\d",
    r"(?P<Series>.*)(?:, Chapter )(?P<Chapter>\d+)",
    r"(?P<Series>.+?)(\s|_|-)(?!Vol)(\s|_|-)((?:Chapter)|(?:Ch\.))(\s|_|-)(?P<Chapter>\d+)",
    r"(?P<Series>.+?):? (\b|_|-)(vol)\.?(\s|-|_)?\d+",
    r"(?P<Series>.+?):?(\s|\b|_|-)Chapter(\s|\b|_|-)\d+(\s|\b|_|-)(vol)(ume)",
    r"(?P<Series>.+?):? (\b|_|-)(vol)(ume)",
    r"(?P<Series>.*)(\bc\d+\b)",
    r"(?P<Series>.*)(?: _|-|\[|\()\s?vol(ume)?",
    r"^(?P<Series>(?!Vol).+?)(?:(ch(apter|\.)(\b|_|-|\s))|sp)\d",
    r"(?P<Series>.*) (\b|_|-)(v|ch\.?|c|s)\d+",
    r"(?P<Series>.*)\s+(?P<Chapter>\d+)\s+(?:\(\d{4}\))\s",
    r"(?P<Series>.*) (-)?(?P<Chapter>\d+(?:.\d+|-\d+)?) \(\d{4}\)",
    r"(?P<Series>.*)(\s|_)(?:Episode|Ep\.?)(\s|_)(?P<Chapter>\d+(?:.\d+|-\d+)?)",
    r"(?P<Series>.*)\(\d",
    r"(?P<Series>.*)(\s|_)\((c\s|ch\s|chapter\s)",
    r"(?P<Series>.+?)(\s|_|\-)+?chapters(\s|_|\-)+?\d+(\s|_|\-)+?",
    r"(?P<Series>.+?)(\s|_|\-)+?\d+(\s|_|\-)\(",
    r"(?P<Series>.*)(v|s)\d+(-\d+)?(_|\s)",
    r"(?P<Series>.*)(v|s)\d+(-\d+)?",
    r"(?P<Series>.*)(_)(v|vo|c|volume)( |_)\d+",
    r"(?P<Series>.*)( |_)(vol\d+)?( |_)(?:Chp\.? ?\d+)",
    r"(?P<Series>.*)( |_)(?:Chp.? ?\d+)",
    r"^(?!Vol)(?P<Series>.*)( |_)Chapter( |_)(\d+)",
    r"^(?!vol)(?P<Series>.*)( |_)(chapters( |_)?)\d+-?\d*",
    r"^(?!Vol\.?)(?P<Series>.*)( |_|-)(?<!-)(episode|chapter|(ch\.?) ?)\d+-?\d*",
    r"^(?!Vol)(?P<Series>.*)ch\d+-?\d?",
    r"(?P<Series>.*)( ?- ?)Ch\.\d+-?\d*",
    r"^(?!Vol)(?!Chapter)(?P<Series>.+?)(-|_|\s|#)\d+(-\d+)?(권|화|話)",
    r"^(?!Vol)(?!Chapter)(?P<Series>.+?)(-|_|\s|#)\d+(-\d+)?",
    r"^(?!Vol\.?)(?!Chapter)(?P<Series>.+?)(\s|_|-)(?<!-)(ch|chapter)?\.?\d+-?\d*",
    r"^(?!Vol)(?P<Series>.*)( |_|-)(ch?)\d+",
    r"(?P<Series>.+?)第(?P<Volume>\d+(?:(\-)\d+)?)巻",
]


class DoujinshiInfo(dict):
    def __init__(self, **kwargs):
        super(DoujinshiInfo, self).__init__(**kwargs)

    def __getattr__(self, item):
        try:
            ret = dict.__getitem__(self, item)
            return ret if ret else 'Unknown'
        except KeyError:
            return 'Unknown'


class Doujinshi(object):
    def __init__(self, name=None, pretty_name=None, id=None, img_id=None,
                 ext='', pages=0, localized_name=None, pretty_localized_name=None, parodies=None, characters=None, artists=None, groups=None, tags=None, name_format='[%i][%a][%t]', **kwargs):
        self.name = name
        self.pretty_name = pretty_name
        self.id = id
        self.img_id = img_id
        self.ext = ext
        self.pages = pages
        self.localized_name = localized_name
        self.pretty_localized_name = pretty_localized_name
        self.parodies = parodies
        self.characters = characters
        self.artists = artists
        self.groups = groups
        self.tags = tags
        self.downloader = None
        self.url = f'{DETAIL_URL}/{self.id}'
        self.info = DoujinshiInfo(**kwargs)

        ag_value = self.groups if self.artists is None else self.artists
        name_format = name_format.replace('%ag', format_filename(ag_value))

        name_format = name_format.replace('%i', format_filename(str(self.id)))
        name_format = name_format.replace('%a', format_filename(self.artists))
        name_format = name_format.replace('%g', format_filename(self.groups))

        name_format = name_format.replace('%t', format_filename(self.name))
        name_format = name_format.replace('%p', format_filename(self.pretty_name))
        name_format = name_format.replace('%s', format_filename(self.localized_name))
        self.filename = format_filename(name_format, 255, True)

        self.table = [
            ['Parodies', self.parodies],
            ['Doujinshi', self.name],
            ['Subtitle', self.localized_name],
            ['Characters', self.characters],
            ['Authors', self.artists],
            ['Groups', self.groups],
            ['Languages', self.info.languages],
            ['Tags', self.tags],
            ['URL', self.url],
            ['Pages', self.pages],
        ]

    def __repr__(self):
        return f'<Doujinshi: {self.name}>'

    def show(self):
        logger.info(f'Print doujinshi information of {self.id}\n{tabulate(self.table)}')

    def download(self, regenerate_cbz=False):
        logger.info(f'Starting to download doujinshi: {self.name}')
        if self.downloader:
            download_queue = []
            if len(self.ext) != self.pages:
                logger.warning('Page count and ext count do not equal')

            for i in range(1, min(self.pages, len(self.ext)) + 1):
                download_queue.append(f'{IMAGE_URL}/{self.img_id}/{i}.{self.ext[i-1]}')

            self.downloader.start_download(download_queue, self.filename, regenerate_cbz=regenerate_cbz)
        else:
            logger.critical('Downloader has not been loaded')

    # https://github.com/Kareadita/Kavita/blob/develop/API/Services/Tasks/Scanner/Parser/Parser.cs#L690
    def parseseries(self, text=None):
        for regex in MANGA_SERIES_REGEX:
            matches: re.Match = re.match(regex, text, re.IGNORECASE)
            if matches is None:
                continue
            group = matches.group('Series')
            if group is not None:
                return self.cleantitle(group)
    
    def cleantitle(self, text: str):
        text = text.replace("_", " ")

        text = re.sub(r"\b(?:Omnibus(?:\s?Edition)?|Uncensored)\b", "", text, re.IGNORECASE)

        text = re.sub(r"\b(?:{Specials?|One[- ]?Shot|Extra(?:\sChapter)?(?=\s)|Art Collection|Side Stories|Bonus}|Omake)\b", "", text, re.IGNORECASE)

        text = text.strip('\0\t\r -,')

        text = re.sub(r"\s{2,}", " ", text, re.IGNORECASE)

        return text

if __name__ == '__main__':
    test = Doujinshi(name='test nhentai doujinshi', id=1)
    print(test)
    test.show()
    try:
        test.download()
    except Exception as e:
        print(f'Exception: {e}')
