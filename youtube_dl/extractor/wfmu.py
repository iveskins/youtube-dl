# coding: utf-8
from __future__ import unicode_literals

import re
import json
import hashlib
import uuid

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    int_or_none,
    str_or_none,
    str_to_int,
    sanitized_Request,
    unified_strdate,
    urlencode_postdata,
    xpath_text,
)
from ..compat import (
    compat_str,
)


class WfmuRecentMp3ArchiveShowIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?wfmu\.org/listen\.m3u\?archive=(?P<archive>[0-9]+)&show=(?P<show>[0-9]+)'
    _TEST = {
        'url': 'https://wfmu.org/listen.m3u?show=46252&archive=79732',
        'info_dict': {
            'url': 'http://mp3archives.wfmu.org/archive/kdb/mp3jump2010.mp3/0:7:28/0/HA/ha120626.mp3',
            'id': '46252-79732',
            'id': 'listen',
            'ext': 'mp4',
            #'title': 'Miracle Nutrition with Hearty White from 6/26/2012'
            'title': 'listen'
        }
    }
    IE_DESC = "Wfmu.org freeform radio program archived show"
    IE_NAME = "wfmu:show"

    def _text_or_none(self, v, default="NA"):
        return default if v is None else v.text

    def _match_group(self, url, group_name):
        if '_VALID_URL_RE' not in self.__dict__:
            self._VALID_URL_RE = re.compile(self._VALID_URL)
        m = self._VALID_URL_RE.match(url)
        assert m
        return compat_str(m.group(group_name))

    def _add_chapter(self, start_time, end_time, title):
        end_time   = float_or_none(end_time,   1000)
        start_time = float_or_none(start_time, 1000)
        #self.report_extraction(start_time)
        #self.report_extraction(end_time)
        if start_time is None or end_time is None:
            self.report_extraction('nope')
            return
        #chapters.append({
        return {
            'start_time':  start_time,
            'end_time':    end_time,
            'title':       title, 
        }


    def _extract_segments(self, playlist):
          return playlist.findall('./segment')

    def _extract_chapters(self, playlist):
        segments = self._extract_segments(playlist)
        #self.report_extraction(segments)
        chapters = []
        for segment, next_segment in zip(segments, segments[1:]):
            artist = self._text_or_none(segment.find('artist'), "NA")
            title =  self._text_or_none(segment.find('title'), "Untitled")
            starttime = str_or_none(segment.find('startTime').get('msec'),'0')
            endtime = str_or_none(next_segment.find('startTime').get('msec'), starttime)

            if starttime is '':
                starttime = '0'
            if endtime is '':
                endtime = starttime
            #if artist is None:
            #    artist = 'NA'
            #else:
            #    artist = artist.text

            #if title is None:
            #    title = 'Untitled'
            #else:
            #    title = title.text

            #self.report_extraction(artist)
            chapters.append(self._add_chapter(
                   starttime,
                   endtime, 
                   '{artist} - {title}'.format(
                       artist=artist, title=title)
                   ))
#          chapters.append({
#              'start_time': start_time,
#              'end_time:': end_time,
#              'title': chapter_title,
#          })
        last_segment = segments[-1]
        chapters.append(self._add_chapter(
            str_or_none(last_segment.find('startTime').get('msec'), '0'),
            str_or_none(last_segment.find('startTime').get('msec'), '0'),
            '{artist} - {title}'.format(
                    artist=self._text_or_none(last_segment.find('artist'), "NA"), 
                    title=self._text_or_none(last_segment.find('title'), "Unknown")
                    ),
                )) 
        #self.report_extraction(chapters[-1])
        return chapters

    def _real_extract(self, url):


        show_id = self._match_group(url,'show')
        archive_id = self._match_group(url,'archive')
        show_playlist_url = 'https://wfmu.org/playlists/shows/' + show_id + '/starttimes.xml'
        
        #[generic] x: Requesting header
        #self.to_screen('%s: Requesting header' %show_id)
        formats = self._extract_m3u8_formats(url, show_id, 'mp4') 

        #[generic] listen: Downloading m3u8 information
        

        self.to_screen('get webpage as a string')
        webpage = self._download_webpage(url, show_id)
        #show_playlist_xml = self._download_xml(show_playlist_url, show_id, 'Downloading playlist')
        show_playlist = self._download_xml(show_playlist_url, show_id, 'Downloading playlist')
        #show_playlist = self._parse_xml(show_playlist_xml, show_id)

        self.report_extraction(show_id)
        self.report_extraction(archive_id)
        self.report_extraction(show_playlist_url)

        # like http://mp3archives.wfmu.org/archive/kdb/mp3jump2010.mp3/0:7:58/0/ED/ed200520.mp3
        #self.report_extraction(webpage.strip())
        audio_url = webpage.strip()

        chapters = self._extract_chapters(show_playlist)
        self.report_extraction(chapters)

        info_dict = {
            'id':           show_id + '-' +  archive_id,
            'url':          audio_url,
            'chapters':     chapters,
            'title':        "example",
            'extractor':    'generic',
            'formats':      formats,
        }
        return info_dict

