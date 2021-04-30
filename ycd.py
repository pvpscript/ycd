import os
import re
import sys
import shutil

import youtube_dl

class YoutubeChannelDownloader:
    _channel_playlists = lambda self, c: f'https://www.youtube.com/c/{c}/playlists'
    _channel_url = lambda self, c: f'https://www.youtube.com/c/{c}/videos'

    _dangerous_characters = r"[/\\?:*<>|]"

    _not_found = []

    def __init__(self, channel, local_vids_path='videos', playlists_dest_path='playlists'):
        self._channel = channel

        self._local_vids_path = local_vids_path
        self._playlists_dest_path = playlists_dest_path

    def download_videos(self):
        pass

    def _get_local_videos(self):
        EXT_LEN = 4
        ID_LEN = 11

        vids_dict = {}

        videos = os.listdir(path=self._local_vids_path)
        for v in videos:
            id = v[-(ID_LEN+EXT_LEN):-EXT_LEN]
            vid_path = os.path.abspath(os.path.join(self._local_vids_path, v))

            vids_dict[id] = vid_path 

        return vids_dict

    def _match_file_times(self, original_path, symlink_path):
        stat = os.stat(original_path)
        os.utime(symlink_path, times=(stat.st_atime, stat.st_mtime), follow_symlinks=False)

    def organize_local_playlists(self):
        videos = self._get_local_videos()

        ydl_opts = { 'extract_flat': True }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ch_info = ydl.extract_info(self._channel_playlists(self._channel), download=False)

            for ch_entry in ch_info['entries']:
                pl_info = ydl.extract_info(ch_entry['url'], download=False)

                folder_name = re.sub(self._dangerous_characters, "_", pl_info['title'])
                folder_path = os.path.abspath(os.path.join(self._playlists_dest_path, folder_name))
                os.makedirs(folder_path, exist_ok=True)

                for pl_entry in pl_info['entries']:
                    vid_title = pl_entry['title']

                    try:
                        abs_src = videos[pl_entry['id']]
                        dst = os.path.join(folder_path, os.path.basename(abs_src))
                        src_rel_dst = os.path.relpath(abs_src, os.path.dirname(dst))

                        os.symlink(src_rel_dst, dst)
                        self._match_file_times(abs_src, dst)

                        print(f'{src_rel_dst} -> {dst}')
                    except KeyError:
                        print(f'Video not found for key {pl_entry["id"]}', file=sys.stderr)
                        self._not_found.append({ pl_entry['id']: vid_title })
                    except FileExistsError:
                        pass

    @property
    def not_found(self):
        return self._not_found

if __name__ == '__main__':
    downloader = YoutubeChannelDownloader("")

    downloader.organize_local_playlists()
    print(downloader.not_found)

# fetch_playlists_info ##-> filter out playlists that doesn't belong to the channel's owner
# fetch_channel_info
# filter out videos that were already downloaded to lower youtube-dl's fetching time
# download_videos
# organize_local_playlists
