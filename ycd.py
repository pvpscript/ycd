import os
import re
import sys
import shutil

import youtube_dl

from collections import namedtuple

Symlink = namedtuple('Symlink', ['abs_src', 'rel_src', 'dst'])

class InformationHandler:
    _ext_len = 4 # ".mp4" extension
    _id_len = 11 # youtube's default video id length

    _channel_playlists = lambda self, c: f'https://www.youtube.com/c/{c}/playlists'
    _channel_videos = lambda self, c: f'https://www.youtube.com/c/{c}/videos'

    _dangerous_characters = r'[/\\?:*<>|]'

    def __init__(self, channel, local_vids_path='videos', playlists_dest_path='playlists'):
        self._ydl_opts = { 'extract_flat': True }
        self._channel = channel

        self._local_vids_path = local_vids_path
        self._playlists_dest_path = playlists_dest_path
    
        self._not_found = []

        #self._local_videos = self._get_local_videos()
        #self._videos_data = self._fetch_videos_data(self._local_videos)
        #self._playlists_data = self._fetch_playlists_data(self._local_videos)

    def _get_local_videos(self):
        vids_dict = {}

        videos = os.listdir(path=self._local_vids_path)
        for v in videos:
            id = v[-(self._id_len+self._ext_len):-self._ext_len]
            vid_path = os.path.abspath(os.path.join(self._local_vids_path, v))

            vids_dict[id] = vid_path 

        return vids_dict

    def fetch_videos_data(self):
        local_videos = self._get_local_videos()

        with youtube_dl.YoutubeDL(self._ydl_opts) as ydl:
            ch_info = ydl.extract_info(self._channel_videos(self._channel), download=False)

            return [v['url'] for v in ch_info['entries'] if v['id'] not in local_videos]

    def fetch_playlists_data(self):
        local_videos = self._get_local_videos()
        data = {}

        with youtube_dl.YoutubeDL(self._ydl_opts) as ydl:
            ch_info = ydl.extract_info(self._channel_playlists(self._channel), download=False)

            for ch_entry in ch_info['entries']:
                pl_info = ydl.extract_info(ch_entry['url'], download=False)

                folder_name = re.sub(self._dangerous_characters, "_", pl_info['title'])
                folder_path = os.path.abspath(os.path.join(self._playlists_dest_path, folder_name))
                #os.makedirs(folder_path, exist_ok=True)
                data[folder_path] = []

                for pl_entry in pl_info['entries']:
                    vid_title = pl_entry['title']

                    try:
                        abs_src = local_videos[pl_entry['id']]
                        dst = os.path.join(folder_path, os.path.basename(abs_src))
                        src_rel_dst = os.path.relpath(abs_src, os.path.dirname(dst))

                        #os.symlink(src_rel_dst, dst)
                        #self._match_file_times(abs_src, dst)
                        data[folder_path].append(Symlink(abs_src, src_rel_dst, dst))

                        print(f'{src_rel_dst} -> {dst}')
                    except KeyError:
                        print(f'Video not found for key {pl_entry["id"]}', file=sys.stderr)
                        self._not_found.append({ pl_entry['id']: vid_title })
                    except FileExistsError:
                        pass
        return data

    @property
    def local_vids_path(self):
        return self._local_vids_path

    @property
    def not_found(self):
        return self._not_found


class YoutubeChannelDownloader:
    def __init__(self, information_handler):
        self._info_handler = info_handler 

        self._local_vids_path = self._info_handler.local_vids_path
        #self._playlists_dest_path = self._info_handler.playlists_dest_path

        #self._not_found = []

    def download_videos(self):
        pass

    def _match_file_times(self, original_path, symlink_path):
        stat = os.stat(original_path)
        os.utime(symlink_path, times=(stat.st_atime, stat.st_mtime), follow_symlinks=False)

#    def organize_local_playlists(self):
#        videos = self._get_local_videos()
#
#        ydl_opts = { 'extract_flat': True }
#        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
#            ch_info = ydl.extract_info(self._channel_playlists(self._channel), download=False)
#
#            for ch_entry in ch_info['entries']:
#                pl_info = ydl.extract_info(ch_entry['url'], download=False)
#
#                folder_name = re.sub(self._dangerous_characters, "_", pl_info['title'])
#                folder_path = os.path.abspath(os.path.join(self._playlists_dest_path, folder_name))
#                os.makedirs(folder_path, exist_ok=True)
#
#                for pl_entry in pl_info['entries']:
#                    vid_title = pl_entry['title']
#
#                    try:
#                        abs_src = videos[pl_entry['id']]
#                        dst = os.path.join(folder_path, os.path.basename(abs_src))
#                        src_rel_dst = os.path.relpath(abs_src, os.path.dirname(dst))
#
#                        os.symlink(src_rel_dst, dst)
#                        self._match_file_times(abs_src, dst)
#
#                        print(f'{src_rel_dst} -> {dst}')
#                    except KeyError:
#                        print(f'Video not found for key {pl_entry["id"]}', file=sys.stderr)
#                        self._not_found.append({ pl_entry['id']: vid_title })
#                    except FileExistsError:
#                        pass

    @property
    def not_found(self):
        return self._info_handler.not_found

if __name__ == '__main__':
    info_handler = InformationHandler(sys.argv[1])
    downloader = YoutubeChannelDownloader(info_handler)

    #downloader.organize_local_playlists()
    videos_data = info_handler.fetch_videos_data()
    playlists_data = info_handler.fetch_playlists_data()
    not_found = downloader.not_found
    
    import json
    print("\n--------------------------------------------------------------------------------\n")
    print(json.dumps(videos_data, indent=4))
    print("\n--------------------------------------------------------------------------------\n")
    print(json.dumps(playlists_data, indent=4))
    print("\n--------------------------------------------------------------------------------\n")
    print(json.dumps(not_found, indent=4))
    print("\n--------------------------------------------------------------------------------\n")


# fetch_playlists_info ##-> filter out playlists that doesn't belong to the channel's owner
# fetch_channel_info
# filter out videos that were already downloaded to lower youtube-dl's fetching time
# download_videos
# organize_local_playlists
