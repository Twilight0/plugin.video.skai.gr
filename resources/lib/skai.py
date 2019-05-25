# -*- coding: utf-8 -*-

'''
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

from datetime import datetime, timedelta
import json, re
from tulip import bookmarks, directory, client, cache, control, youtube, workers
from youtube_resolver import resolve as yt_resolver
from tulip.compat import urljoin


class indexer:

    def __init__(self):

        self.list = []; self.data = []
        self.base_link = 'http://www.skaitv.gr'
        self.old_base = 'http://www.skai.gr'
        self.yt_channel = 'UCmHgxU394HiIAsN1fMegqzw'
        self.yt_key = 'AIzaSyBOS4uSyd27OU0XV2KSdN3vT2UG_v0g9sI'
        self.tvshows_link = ''.join([self.base_link, '/json/shows.php'])
        self.episodes_link = ''.join([self.base_link, '/json/show.php?caption={0}&cat_caption={1}&cat_caption2={2}'])
        self.episode_link = ''.join([self.base_link, '/json/episode.php?caption=no&show_caption={0}&epanalipsi={1}&cat_caption2={2}'])
        self.live_link = ''.join([self.base_link, '/json/live.php'])
        self.podcasts_link = ''.join([self.old_base, '/Ajax.aspx?m=Skai.TV.ProgramListView&la=0&Type=Radio&Day=%s'])
        self.sports_link = ''.join([self.old_base, '/Ajax.aspx?m=Skai.Player.ItemView&cid=6&alid=14'])
        self.old_episodes_link = ''.join([self.old_base, '/Ajax.aspx?m=Skai.Player.ItemView&cid=6&alid=%s'])
        self.play_link = 'http://videostream.skai.gr{0}'
        self.radio_link = 'http://liveradio.skai.gr/skaihd/skai/playlist.m3u8'

    def root(self, audio_only=False):

        self.list = [
            {
                'title': control.lang(32001),
                'action': 'live',
                'isFolder': 'False',
                'icon': 'live.png'
            }
            ,
            {
                'title': control.lang(32014),
                'action': 'play',
                'url': self.radio_link,
                'isFolder': 'False',
                'icon': 'live.png'
            }
            ,
            {
                'title': control.lang(32002),
                'action': 'tvshows',
                'icon': 'tvshows.png'
            }
            ,
            {
                'title': control.lang(32003),
                'action': 'podcasts',
                'icon': 'podcasts.png'
            }
            ,
            {
                'title': control.lang(32004),
                'action': 'archive',
                'icon': 'archive.png'
            }
            ,
            {
                'title': control.lang(32005),
                'action': 'popular',
                'icon': 'popular.png'
            }
            ,
            {
                'title': control.lang(32006),
                'action': 'news',
                'icon': 'news.png'
            }
            ,
            {
                'title': control.lang(32007),
                'action': 'sports',
                'icon': 'sports.png'
            }
            ,
            {
                'title': control.lang(32008),
                'action': 'bookmarks',
                'icon': 'bookmarks.png'
            }
        ]

        if audio_only:

            self.list = [self.list[1]] + [self.list[3]]

        for item in self.list:
            cache_clear = {'title': 32009, 'query': {'action': 'cache_clear'}}
            item.update({'cm': [cache_clear]})

        directory.add(self.list, content='videos')

    def bookmarks(self):

        self.list = bookmarks.get()

        if self.list is None:
            return

        for i in self.list:
            bookmark = dict((k, v) for k, v in i.iteritems() if not k == 'next')
            bookmark['delbookmark'] = i['url']
            i.update({'cm': [{'title': 32502, 'query': {'action': 'deleteBookmark', 'url': json.dumps(bookmark)}}]})

        self.list = sorted(self.list, key=lambda k: k['title'].lower())

        directory.add(self.list, content='videos')

    def archive(self):

        self.list = cache.get(youtube.youtube(key=self.yt_key).playlists, 12, self.yt_channel)

        if self.list is None:
            return

        for i in self.list:

            i.update({'action': 'episodes'})
            bookmark = dict((k, v) for k, v in i.iteritems() if not k == 'next')
            bookmark['bookmark'] = i['url']
            i.update({'cm': [{'title': 32501, 'query': {'action': 'addBookmark', 'url': json.dumps(bookmark)}}]})

        control.sortmethods('title')

        directory.add(self.list, content='videos')

    def tvshows(self):

        self.list = cache.get(self.generic_listing, 24, self.tvshows_link)

        if self.list is None:
            return

        for i in self.list: i.update({'action': 'episodes'})

        for i in self.list:

            bookmark = dict((k, v) for k, v in i.iteritems() if not k == 'next')
            bookmark['bookmark'] = i['url']
            i.update({'cm': [{'title': 32501, 'query': {'action': 'addBookmark', 'url': json.dumps(bookmark)}}]})

        control.sortmethods('title')

        directory.add(self.list, content='videos')

    def podcasts(self):

        self.list = cache.get(self.old_listing, 24, self.podcasts_link)

        if self.list is None:
            return

        for i in self.list:

            i.update({'action': 'old_episodes'})

        for i in self.list:

            bookmark = dict((k, v) for k, v in i.iteritems() if not k == 'next')
            bookmark['bookmark'] = i['url']

            i.update({'cm': [{'title': 32501, 'query': {'action': 'addBookmark', 'url': json.dumps(bookmark)}}]})

        control.sortmethods('title')

        directory.add(self.list, content='videos')

    def episodes(self, url):

        if url.startswith('http'):
            self.list = cache.get(self.episodes_listing, 1, url)
        else:
            self.list = cache.get(youtube.youtube(key=self.yt_key).playlist, 2, url)

        if self.list is None:

            return

        for i in self.list:

            i.update({'action': 'play', 'isFolder': 'False'})

        directory.add(self.list, content='videos')

    def popular(self):

        self.list = cache.get(youtube.youtube(key=self.yt_key).videos, 1, self.yt_channel, False, 2)

        if self.list is None:
            return

        self.list = [i for i in self.list if int(i['duration']) > 60]

        for i in self.list:
            i.update({'action': 'play', 'isFolder': 'False'})

        directory.add(self.list)

    def news(self):

        self.list = [
            {
                'title': control.lang(32011),
                'action': 'episodes',
                'icon': 'news.png',
                'url': ''.join([self.base_link, '/json/show.php?caption=sezon-2018-2019&cat_caption=enimerosi&cat_caption2=oi-eidiseis-tou-ska-stis-2'])
            }
            ,
            {
                'title': control.lang(32012),
                'action': 'episodes',
                'icon': 'news.png',
                'url': ''.join([self.base_link, '/json/show.php?caption=sezon-2018-2019&cat_caption=enimerosi&cat_caption2=ta-nea-tou-ska-stis-2000'])
            }
            ,
            {
                'title': control.lang(32013),
                'action': 'episodes',
                'icon': 'news.png',
                'url': ''.join([self.base_link, '/json/show.php?caption=sezon-2018-2019&cat_caption=enimerosi&cat_caption2=deltio-sti-noimatiki'])
            }
        ]

        directory.add(self.list, content='videos')

    def sports(self):

        self.old_episodes(self.sports_link)

    def play(self, url):

        play_object = self.resolve(url)

        if len(play_object) == 2:

            stream, plot = play_object
            meta = {'plot': plot}

        else:

            stream = play_object
            meta = None

        if url == self.radio_link:

            meta = {'title': 'Skai Radio 100.3FM'}

        directory.resolve(url=stream, meta=meta, dash='dash' in stream or '.mpd' in stream)

    def live(self):

        stream = self.resolve(self.resolve_live())

        directory.resolve(stream, meta={'title': 'SKAI'}, dash='dash' in stream or '.mpd' in stream)

    def old_listing(self, url):

        u = []
        d = datetime.utcnow()

        for i in range(0, 7):
            u.append(url % d.strftime('%d.%m.%Y'))
            d = d - timedelta(hours=24)

        u = u[::-1]

        threads = []

        for i in range(0, 7):

            threads.append(workers.Thread(self.thread, u[i], i))
            self.data.append('')

        [i.start() for i in threads]
        [i.join() for i in threads]

        items = ''.join(self.data)

        items = client.parseDOM(items, 'Show', attrs={'TVonly': '0'})

        for item in items:

            title = client.parseDOM(item, 'Show')[0]
            title = title.split('[')[-1].split(']')[0]
            title = client.replaceHTMLCodes(title)
            title = title.encode('utf-8')

            url = client.parseDOM(item, 'Link')[0]
            url = url.split('[')[-1].split(']')[0]
            url = urljoin(self.old_base, url)
            url = client.replaceHTMLCodes(url)
            url = url.encode('utf-8')

            image = client.parseDOM(item, 'ShowImage')[0]
            image = image.split('[')[-1].split(']')[0]
            image = urljoin(self.base_link, image)
            image = client.replaceHTMLCodes(image)
            image = image.encode('utf-8')

            if image in str(self.list):
                continue

            if 'mmid=' not in url:
                continue

            self.list.append({'title': title, 'url': url, 'image': image})

        return self.list

    def generic_listing(self, url):

        json_object = json.loads(client.request(url))

        shows = json_object['shows'] + json_object['now_shows']

        for show in shows:

            if '/category/' in show['link']:
                continue

            title = ' - '.join([show['title'], show['subtitle']])
            image = ''.join(['http:', show['img']])

            url = self.episodes_link.format(show['caption'], show['link'].split('/')[2], show['catcaption'])

            self.list.append({'title': title, 'url': url, 'image': image})

        return self.list

    def old_episodes_listing(self, url):

        xml = client.request(url)

        if 'ItemView' not in url:

            try:
                url = client.parseDOM(xml, 'li', ret='id', attrs={'class': 'active_sub'})[0]
            except IndexError:
                return control.infoDialog(control.lang(32010))

            url = self.old_episodes_link % url

            threads = []

            for i in range(1, 10):

                threads.append(workers.Thread(self.thread, url + '&Page=%s' % str(i), i))
                self.data.append('')

            [i.start() for i in threads]
            [i.join() for i in threads]

            items = ''.join(self.data)

            items = client.parseDOM(items, 'Item')

        else:

            items = client.parseDOM(xml, 'Item')

        for item in items:

            date = client.parseDOM(item, 'Date')[0]
            date = date.split('[')[-1].split(']')[0]
            date = date.split('T')[0]

            title = client.parseDOM(item, 'Title')[0]
            title = title.split('[')[-1].split(']')[0]
            title = '%s (%s)' % (title, date)
            title = client.replaceHTMLCodes(title)
            title = title.encode('utf-8')

            url = client.parseDOM(item, 'File')[0]
            url = url.split('[')[-1].split(']')[0]
            url = client.replaceHTMLCodes(url)
            url = url.encode('utf-8')

            image = client.parseDOM(item, 'Photo1')[0]
            image = image.split('[')[-1].split(']')[0]
            image = urljoin(self.old_base, image)
            image = client.replaceHTMLCodes(image)
            image = image.encode('utf-8')

            self.list.append({'title': title, 'url': url, 'image': image})

        return self.list

    def old_episodes(self, url):

        self.list = cache.get(self.old_episodes_listing, 1, url)

        if self.list is None:
            return

        for i in self.list:

            i.update({'action': 'play', 'isFolder': 'False'})

        directory.add(self.list, content='videos')

    def episodes_listing(self, url):

        json_object = json.loads(client.request(url))

        episodes_list = json_object['episodes']

        for episode in episodes_list:

            title = episode['title']
            date = episode['start'].split()[0]
            image = ''.join(['http:', episode['img']])
            media_item_file = episode['media_item_file']

            if media_item_file is None or media_item_file.endswith('.flv'):

                url = self.episode_link.format(episode['link'].rsplit('/')[-1], '', episode['link'].rsplit('/')[-2])

            else:

                url = self.play_link.format('/' + media_item_file if not media_item_file.startswith('/') else media_item_file)

                url += '.m3u8'

            plot = episode['short_descr']

            self.list.append({'title': ' - '.join([title, date]), 'url': url, 'image': image, 'plot': plot})

        return self.list

    def resolve(self, url):

        if url.startswith('rtmp'):

            p = re.findall('/([a-zA-Z0-9]{3,}:)', url)

            if len(p) > 0:
                url = url.replace(p[0], ' playpath={0}'.format(p[0]))

            url += ' timeout=10'

            return url

        elif len(url) == 11:

            link = 'plugin://plugin.video.youtube/play/?video_id={0}'.format(url)

            return link

        elif 'json' in url:

            json_object = json.loads(client.request(url))

            plot = client.stripTags(json_object['episode'][0]['descr'])
            media_item_file = json_object['episode'][0]['media_item_file']

            if media_item_file.endswith('.mp4'):

                stream = self.play_link.format('/' + media_item_file if not media_item_file.startswith('/') else media_item_file)

                stream += '.m3u8'

            else:

                youtu_id = json_object['episode'][0]['media_item_file']

                stream = self.yt_session(youtu_id)

            return stream, plot

        elif 'episode' in url and not '.php' in url:

            parts = url.split('/')

            return self.resolve(self.episode_link.format(parts[-1], '', parts[-2]))

        else:

            return url

    def resolve_live(self):

        json_object = json.loads(client.request(self.live_link))

        youtu_id = json_object['now']['livestream']

        stream = self.yt_session(youtu_id)

        return stream

    @staticmethod
    def yt_session(yt_id):

        streams = yt_resolver(yt_id)

        try:
            addon_enabled = control.addon_details('inputstream.adaptive').get('enabled')
        except KeyError:
            addon_enabled = False

        if not addon_enabled:

            streams = [s for s in streams if 'mpd' not in s['title']]

        stream = streams[0]['url']

        return stream

    def thread(self, url, i):

        try:

            result = client.request(url)
            self.data[i] = result

        except:


            return
