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

import json, re
from tulip import bookmarks, directory, client, cache, control, youtube
from tulip.compat import zip, iteritems
from youtube_resolver import resolve as yt_resolver


class Indexer:

    def __init__(self):

        self.list = []; self.data = []
        self.base_link = 'http://www.skaitv.gr'
        self.old_base = 'http://www.skai.gr'
        self.radio_base = 'http://www.skairadio.gr'
        self.yt_channel = 'UCmHgxU394HiIAsN1fMegqzw'
        self.yt_key = 'AIzaSyBOS4uSyd27OU0XV2KSdN3vT2UG_v0g9sI'
        self.tvshows_link = ''.join([self.base_link, '/shows/seires'])
        self.entertainment_link = ''.join([self.base_link, '/shows/psuchagogia'])
        self.news_link = ''.join([self.base_link, '/shows/enimerosi'])
        self.live_link = ''.join([self.base_link, '/live'])
        self.podcasts_link = ''.join([self.radio_base, '/shows?page=0'])
        self.play_link = 'http://videostream.skai.gr/'
        self.radio_link = 'http://liveradio.skai.gr/skaihd/skai/playlist.m3u8'

    def root(self, audio_only=False):

        self.list = [
            {
                'title': control.lang(32001),
                'action': 'play',
                'isFolder': 'False',
                'icon': 'live.png',
                'url': self.live_link
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
                'action': 'shows',
                'icon': 'tvshows.png',
                'url': self.tvshows_link
            }
            ,
            {
                'title': control.lang(32015),
                'action': 'shows',
                'icon': 'entertainment.png',
                'url': self.entertainment_link
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
                'action': 'latest',
                'icon': 'latest.png'
            }
            ,
            {
                'title': control.lang(32006),
                'action': 'news',
                'icon': 'news.png'
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
            bookmark = dict((k, v) for k, v in iteritems(i) if not k == 'next')
            bookmark['delbookmark'] = i['url']
            i.update({'cm': [{'title': 32502, 'query': {'action': 'deleteBookmark', 'url': json.dumps(bookmark)}}]})

        self.list = sorted(self.list, key=lambda k: k['title'].lower())

        directory.add(self.list, content='videos')

    def archive(self):

        self.list = cache.get(youtube.youtube(key=self.yt_key).playlists, 12, self.yt_channel)

        if self.list is None:
            return

        for i in self.list:
            i['title'] = client.replaceHTMLCodes(i['title'])
            i.update({'action': 'episodes'})
            bookmark = dict((k, v) for k, v in iteritems(i) if not k == 'next')
            bookmark['bookmark'] = i['url']
            i.update({'cm': [{'title': 32501, 'query': {'action': 'addBookmark', 'url': json.dumps(bookmark)}}]})

        control.sortmethods('title')

        directory.add(self.list, content='videos')

    def shows(self, url):

        self.list = cache.get(self.generic_listing, 24, url)

        if self.list is None:
            return

        for i in self.list:

            i.update({'action': 'episodes'})

            bookmark = dict((k, v) for k, v in iteritems(i) if not k == 'next')
            bookmark['bookmark'] = i['url']

            i.update({'cm': [{'title': 32501, 'query': {'action': 'addBookmark', 'url': json.dumps(bookmark)}}]})

        directory.add(self.list, content='videos')

    def pod_listing(self, url):

        html = client.request(url)

        listing = client.parseDOM(html, 'div', attrs={'class': 'row border-bottom pt-4 m-0 show-item'})

        nexturl = re.sub(r'\d(?!\d)', lambda x: str(int(x.group(0)) + 1), url)

        for item in listing:

            title = client.parseDOM(item, 'h3')[0].replace('&#039;', '\'')
            image = ''.join([self.radio_base, client.parseDOM(item, 'img', ret='src')[0]])
            url = ''.join([self.radio_base, client.parseDOM(item, 'a', ret='href')[0]])

            self.list.append(
                {
                    'title': title, 'image': image, 'url': url, 'nextaction': 'podcasts', 'next': nexturl,
                    'nextlabel': 32500
                }
            )

        return self.list

    def podcasts(self, url=None):

        if url is None:
            url = self.podcasts_link

        self.list = cache.get(self.pod_listing, 24, url)

        if self.list is None:
            return

        for i in self.list:

            i.update({'action': 'episodes'})

            bookmark = dict((k, v) for k, v in iteritems(i) if not k == 'next')
            bookmark['bookmark'] = i['url']

            i.update({'cm': [{'title': 32501, 'query': {'action': 'addBookmark', 'url': json.dumps(bookmark)}}]})

        directory.add(self.list, content='music')

    def pod_episodes(self, url):

        html = client.request(url)

        select = client.parseDOM(html, 'div', attrs={'class': 'col-8 col-sm-4 p-0'})[0]
        image = re.search(r'background-image: url\("(.+?)"\)', html).group(1)

        pods = re.findall(r'(<option.+?option>)', select, re.S)

        for pod in pods:

            date = re.search(r'(\d{2}/\d{2}/\d{4})', pod).group(1)
            title = ' - '.join([client.parseDOM(html, 'h2', attrs={'class': 'mb-3.+?'})[0], date])
            url = ''.join([self.radio_base, re.search(r'data-url = "([\w\-/]+)"', pod).group(1)])

            self.list.append({'title': title, 'image': image, 'url': url})

        return self.list

    def episodes(self, url):

        if self.base_link in url:
            self.list = cache.get(self.episodes_listing, 3, url)
        elif self.radio_base in url:
            self.list = cache.get(self.pod_episodes, 3, url)
        else:
            self.list = cache.get(youtube.youtube(key=self.yt_key).playlist, 3, url)

        if self.list is None:

            return

        for i in self.list:

            i.update({'action': 'play', 'isFolder': 'False'})

        directory.add(self.list, content='videos')

    def video_listing(self, url):

        html = client.request(url)

        try:
            nexturl = ''.join(
                [
                    self.old_base, '/videos',
                    client.parseDOM(html, 'a', attrs={'rel': 'next'}, ret='href')[0].replace('&amp;', '&')
                ]
            )
        except IndexError:
            nexturl = None

        video_list = client.parseDOM(html, 'div', attrs={'class': 'videoItem cell'}, ret='data-video-url')
        thumbnails = client.parseDOM(html, 'div', attrs={'class': 'videoItem cell'}, ret='data-video-poster')
        titles = client.parseDOM(html, 'div', attrs={'class': 'videoItem cell'}, ret='data-video-name')
        dates = client.parseDOM(html, 'div', attrs={'class': 'videoItem cell'}, ret='data-video-date')

        listing = list(zip(titles, dates, thumbnails, video_list))

        for title, date, image, video in listing:

            label = ''.join([title, ' ', '(', date, ')'])

            self.list.append(
                {
                    'title': label, 'image': image, 'url': video, 'next': nexturl, 'nextlabel': 32500,
                    'nextaction': 'videos'
                }
            )

        return self.list

    def videos(self, url):

        self.list = cache.get(self.video_listing, 3, url)

        if self.list is None:
            return

        for i in self.list:

            i.update({'action': 'play', 'isFolder': 'False'})

        directory.add(self.list)

    def latest(self):

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
                'title': 32011,
                'action': 'episodes',
                'icon': 'news.png',
                'url': ''.join([self.base_link, '/show/enimerosi/oi-eidiseis-tou-ska-stis-2/sezon-2019-2020'])
            }
            ,
            {
                'title': 32012,
                'action': 'episodes',
                'icon': 'news.png',
                'url': ''.join([self.base_link, '/show/enimerosi/ta-nea-tou-ska-stis-2000/sezon-2019-2020'])
            }
            ,
            {
                'title': 32005,
                'action': 'videos',
                'icon': 'latest.png',
                'url': ''.join([self.old_base, '/videos?type=recent'])
            }
            ,
            {
                'title': 32016,
                'action': 'videos',
                'icon': 'popular.png',
                'url': ''.join([self.old_base, '/videos?type=popular'])
            }
            ,
            {
                'title': 32017,
                'action': 'videos',
                'icon': 'recommended.png',
                'url': ''.join([self.old_base, '/videos?type=featured'])
            }
        ]

        directory.add(self.list, content='videos')

    def play(self, url):

        resolved = self.resolve(url)

        if isinstance(resolved, tuple):

            stream, plot = resolved
            meta = {'plot': plot}

        else:

            stream = resolved
            meta = None

        icon = None

        if url == self.radio_link:

            meta = {'title': 'Skai Radio 100.3FM'}

        elif url == self.live_link:

            meta = {'title': 'Skai Live TV'}
            icon = control.icon()

        directory.resolve(url=stream, meta=meta, dash='dash' in stream or '.mpd' in stream, icon=icon)

    def generic_listing(self, url):

        html = client.request(url)

        if url == self.news_link:
            new = 'row m-0 listrow new-videos'
            new_items = 'col-12 pl-0 pr-0 list1 list-item color_enimerosi'
            archive = 'row m-0 listrow s234 '
            archived_items = 'col-12 pl-0 pr-0 list1 list-item color_enimerosi'
        elif url == self.entertainment_link:
            new = 'row  listrow list2 '
            new_items = 'd-none d-md-block col-md-4 listimg color_psuchagogia'
            archive = 'row  listrow list2 s234  '
            archived_items = 'd-none d-md-block col-md-3 listimg color_psuchagogia'
        else:
            new = 'row  listrow list2 '
            new_items = 'd-none d-md-block col-md-4 listimg color_seires'
            archive = 'row  listrow list2 s234  '
            archived_items = 'd-none d-md-block col-md-3 listimg color_seires'

        div = client.parseDOM(html, 'div', attrs={'class': new})[0]

        listing = client.parseDOM(div, 'div', attrs={'class': new_items})

        for item in listing:

            title = client.parseDOM(item, 'h3')[0]
            image = client.parseDOM(item, 'img', ret='src')[0]

            url = ''.join([self.base_link, client.parseDOM(item, 'a', ret='href')[0]])

            self.list.append({'title': title, 'url': url, 'image': image})

        if 's234' in html:

            div = client.parseDOM(html, 'div', attrs={'class': archive})[0]
            items = client.parseDOM(div, 'div', attrs={'class': archived_items})

            for item in items:

                title = ' - '.join([client.parseDOM(item, 'h3')[0], control.lang(32013)])
                image = client.parseDOM(item, 'img', ret='src')[0]

                url = ''.join([self.base_link, client.parseDOM(item, 'a', ret='href')[0]])

                self.list.append({'title': title, 'url': url, 'image': image})

        return self.list

    def episodes_listing(self, url):

        html = client.request(url)

        div = client.parseDOM(html, 'div', attrs={'class': 'row  listrow list2 ?'})[0]

        listing = client.parseDOM(div, 'div', attrs={'class': '.+?list-item  color.+?'})

        for item in listing:

            title = client.parseDOM(item, 'h3')[0].replace('<br/>', ' ').replace('<br>', ' ')
            image = client.parseDOM(item, 'img', ret='src')[0]

            url = ''.join([self.base_link, client.parseDOM(item, 'a', ret='href')[0]])

            self.list.append({'title': title, 'url': url, 'image': image})

        return self.list

    def resolve(self, url):

        if url == self.live_link:

            html = client.request(self.live_link)

            json_ = re.search(r'var data = ({.+?});', html).group(1)

            json_ = json.loads(json_)

            youtu_id = json_['now']['livestream']

            stream = self.yt_session(youtu_id)

            return stream

        elif len(url) == 11:

            link = self.yt_session(url)

            return link

        elif 'episode' in url:

            html = client.request(url)

            if url.startswith(self.radio_base):

                url = re.search(r'["\'](.+?\.mp3)["\']', html).group(1)

                return url

            else:

                json_ = re.search(r'var data = ({.+?});', html).group(1)

                json_ = json.loads(json_)

                url = ''.join([self.play_link, json_['episode'][0]['media_item_file'], '.m3u8'])

                plot = client.stripTags(json_['episode'][0]['descr'])

                return url, plot

        else:

            return url

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
