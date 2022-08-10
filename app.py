import ctypes
import json
import sys
from typing import Any, TypedDict, Union, List

from plexapi.server import PlexServer


class DjMdContent(TypedDict):
    id: Union[str, None]
    folder_path: Union[str, None]
    file_name_l: Union[str, None]
    file_name_s: Union[str, None]
    title: Union[str, None]
    artist_id: Union[str, None]
    album_id: Union[str, None]
    genre_id: Union[str, None]
    bpm: Union[int, None]
    length: Union[int, None]
    track_no: Union[int, None]
    bit_rate: Union[int, None]
    bit_depth: Union[int, None]
    commnt: Union[str, None]
    file_type: Union[int, None]
    rating: Union[int, None]
    release_year: Union[int, None]
    remixer_id: Union[str, None]
    label_id: Union[str, None]
    org_artist_id: Union[str, None]
    key_id: Union[str, None]
    stock_date: Union[str, None]
    color_id: Union[str, None]
    dj_play_count: Union[int, None]
    image_path: Union[str, None]
    master_dbid: Union[str, None]
    master_song_id: Union[str, None]
    analysis_data_path: Union[str, None]
    search_str: Union[str, None]
    file_size: Union[int, None]
    disc_no: Union[int, None]
    composer_id: Union[str, None]
    subtitle: Union[str, None]
    sample_rate: Union[int, None]
    disable_quantize: Union[int, None]
    analysed: Union[int, None]
    release_date: Union[str, None]
    date_created: Union[str, None]
    content_link: Union[int, None]
    tag: Union[str, None]
    modified_by_rbm: Union[str, None]
    hot_cue_auto_load: Union[str, None]
    delivery_control: Union[str, None]
    delivery_comment: Union[str, None]
    cue_updated: Union[str, None]
    analysis_updated: Union[str, None]
    track_info_updated: Union[str, None]
    lyricist: Union[str, None]
    isrc: Union[str, None]
    sampler_track_info: Union[int, None]
    sampler_play_offset: Union[int, None]
    sampler_gain: Union[float, None]
    video_associate: Union[str, None]
    lyric_status: Union[int, None]
    service_id: Union[int, None]
    org_folder_path: Union[str, None]
    reserved1: Union[str, None]
    reserved2: Union[str, None]
    reserved3: Union[str, None]
    reserved4: Union[str, None]
    ext_info: Union[str, None]
    rb_file_id: Union[str, None]
    device_id: Union[str, None]
    rb_local_folder_path: Union[str, None]
    src_id: Union[str, None]
    src_title: Union[str, None]
    src_artist_name: Union[str, None]
    src_album_name: Union[str, None]
    src_length: Union[int, None]
    uuid: Union[str, None]
    rb_data_status: Union[int, None]
    rb_local_data_status: Union[int, None]
    rb_local_deleted: Union[int, None]
    rb_local_synced: Union[int, None]
    usn: Union[int, None]
    rb_local_usn: Union[int, None]
    created_at: Any
    updated_at: Any


class DjMdPlaylist(TypedDict):
    id: Union[str, None]
    seq: Union[int, None]
    name: Union[str, None]
    image_path: Union[str, None]
    attribute: Union[int, None]
    parent_id: Union[str, None]
    smart_list: Union[str, None]
    uuid: Union[str, None]
    rb_data_status: Union[int, None]
    rb_local_data_status: Union[int, None]
    rb_local_deleted: Union[int, None]
    rb_local_synced: Union[int, None]
    usn: Union[int, None]
    rb_local_usn: Union[int, None]
    created_at: Any
    updated_at: Any


class PlaylistObj(TypedDict):
    combined_name: str
    dj_md_playlist: DjMdPlaylist
    dj_md_contents: List[DjMdContent]


def get_playlists() -> List[PlaylistObj]:
    library = ctypes.cdll.LoadLibrary('./library.so')
    getPlaylists = library.getPlaylists
    getPlaylists.restype = ctypes.c_void_p

    playlists = getPlaylists()
    playlists_bytes = ctypes.string_at(playlists)
    playlists_str = playlists_bytes.decode('utf-8')
    playlists_parsed = json.loads(playlists_str)

    return playlists_parsed


pl = get_playlists()

if len(sys.argv) <= 2:
    print('Please provide a valid URL and token')
    print('Usage: python3 app.py <server url> <token>')
    sys.exit(0)

token = sys.argv[2]
server_url = sys.argv[1]

plex = PlexServer(server_url, token)

for p in pl:
    playlist_title = p['dj_md_playlist']['name']

    print('syncing', playlist_title)

    tracks = []
    if 'dj_md_contents' not in p or len(p['dj_md_contents']) == 0:
        print('no tracks in playlist', playlist_title)
        continue

    for content in p['dj_md_contents']:
        file_path = content['folder_path']
        file_name = content['file_name_l']
        title = content['title']

        # search for track, by filename and then by title
        found_file = plex.library.search(file=file_name, libtype='track')
        found_name = plex.library.search(title=title, libtype='track')
        if len(found_file) > 0:
            track = found_file[0]
            tracks += [track]
            continue

        if len(found_name) > 0:
            track = found_name[0]
            tracks += [track]
            continue

        print("track not found", title, file_path)

    combined_title = "{}".format(p['combined_name'])
    existing_playlists = plex.playlists(title=combined_title)

    if len(existing_playlists) > 0:
        for track in existing_playlists[0].items():
            try:
                existing_playlists[0].removeItems([track])
            except:
                pass

        existing_playlists[0].addItems(tracks)
        print('updated playlist %s' % combined_title)
        continue

    pl = plex.createPlaylist(title=combined_title, items=tracks)
    print('created playlist %s' % combined_title)

