import argparse
import ctypes
import json
import os
from typing import Any, Dict, List, Tuple, TypedDict, Union

import requests
from plexapi.server import PlexServer

from logger import Logger


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


def _index_plex_track(track: Any, track_map: Dict[str, Any]) -> None:
    """Helper function to index a single track into the track map"""
    # Map by filename
    if hasattr(track, 'media') and track.media:
        for media in track.media:
            for part in media.parts:
                filename = os.path.basename(part.file)
                track_map['by_filename'][filename] = track

    # Map by title (lowercase for better matching)
    if track.title:
        track_map['by_title'][track.title.lower()] = track


def build_plex_track_map(plex: PlexServer, logger: Logger) -> Dict[str, Any]:
    """Build maps of all tracks in Plex for fast lookups"""
    logger.building_track_map()

    track_map = {'by_filename': {}, 'by_title': {}}

    # Get all music sections/libraries
    for section in plex.library.sections():
        if section.type == 'artist':  # Music library
            logger.indexing_library(section.title)
            tracks = section.searchTracks()

            for track in logger.tqdm(
                tracks, desc=f'   Indexing {section.title}', unit=' tracks', leave=False
            ):
                _index_plex_track(track, track_map)

    logger.track_map_complete(len(track_map['by_filename']), len(track_map['by_title']))

    return track_map


def _index_plex_playlist(playlist: Any, playlist_map: Dict[str, Dict]) -> None:
    """Helper function to index a single playlist into the playlist map"""
    if playlist.smart:
        return  # Skip smart playlists

    track_ids = [track.ratingKey for track in playlist.items()]
    playlist_map[playlist.title] = {'playlist': playlist, 'track_ids': track_ids}


def build_plex_playlist_map(plex: PlexServer, logger: Logger) -> Dict[str, Dict]:
    """Build a map of existing Plex playlists with their track IDs"""
    logger.building_playlist_map()

    playlist_map = {}
    playlists = plex.playlists()

    for playlist in logger.tqdm(
        playlists, desc='   Indexing playlists', unit=' playlists'
    ):
        _index_plex_playlist(playlist, playlist_map)

    logger.playlist_map_complete(len(playlist_map))
    return playlist_map


def get_playlists() -> List[PlaylistObj]:
    library = ctypes.cdll.LoadLibrary('./library.so')
    getPlaylists = library.getPlaylists
    getPlaylists.restype = ctypes.c_void_p

    playlists = getPlaylists()
    playlists_bytes = ctypes.string_at(playlists)
    playlists_str = playlists_bytes.decode('utf-8')
    playlists_parsed = json.loads(playlists_str)

    return playlists_parsed


def parse_header(value: str) -> Tuple[str, str]:
    name, sep, header_value = value.partition(':')
    if not sep or not name.strip():
        raise argparse.ArgumentTypeError(f"expected 'Name: Value', got {value!r}")
    return name.strip(), header_value.strip()


pl = get_playlists()


parser = argparse.ArgumentParser(description='Sync rekordbox playlists to Plex')
parser.add_argument(
    'server_url',
    nargs='?',
    default=os.environ.get('PLEX_URL'),
    help='Plex server URL (default: $PLEX_URL)',
)
parser.add_argument(
    'token',
    nargs='?',
    default=os.environ.get('PLEX_TOKEN'),
    help='Plex token (default: $PLEX_TOKEN)',
)
parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
parser.add_argument(
    '-H',
    '--header',
    dest='headers',
    action='append',
    default=[],
    type=parse_header,
    metavar="'Name: Value'",
    help='Extra HTTP header sent with every Plex request (repeatable)',
)
args = parser.parse_args()
if not args.server_url or not args.token:
    parser.error(
        'a Plex server URL and token are required (args or PLEX_URL/PLEX_TOKEN)'
    )

headers = {}
cf_client_id = os.environ.get('CF_ACCESS_CLIENT_ID')
cf_client_secret = os.environ.get('CF_ACCESS_CLIENT_SECRET')
if bool(cf_client_id) != bool(cf_client_secret):
    parser.error('set both CF_ACCESS_CLIENT_ID and CF_ACCESS_CLIENT_SECRET, or neither')
if cf_client_id:
    headers['CF-Access-Client-Id'] = cf_client_id
    headers['CF-Access-Client-Secret'] = cf_client_secret
headers.update(args.headers)

session = requests.Session()
session.headers.update(headers)
plex = PlexServer(args.server_url, args.token, session=session)

# Initialize logger with verbose flag
logger = Logger(verbose=args.verbose)

# Build maps ONCE at the start
track_map = build_plex_track_map(plex, logger)
playlist_map = build_plex_playlist_map(plex, logger)

logger.rekordbox_playlists_found(len(pl))

# Track changes for summary
created_playlists = []
updated_playlists = []
skipped_playlists = []
smart_playlists_skipped = []
not_found_tracks = []  # Track not found tracks for export

for p in logger.tqdm(pl, desc='Syncing playlists', unit='playlist'):
    playlist_title = p['dj_md_playlist']['name']

    # Skip smart playlists
    smart_list_data = p['dj_md_playlist'].get('smart_list')
    if smart_list_data and smart_list_data != '':
        logger.skipping_smart_playlist(playlist_title)
        smart_playlists_skipped.append(playlist_title)
        continue

    logger.processing_playlist(playlist_title)

    if 'dj_md_contents' not in p or len(p['dj_md_contents']) == 0:
        combined_title = '{}'.format(p['combined_name'])
        logger.no_tracks_in_playlist(playlist_title)
        skipped_playlists.append({'name': combined_title, 'reason': 'No tracks'})
        continue

    combined_title = '{}'.format(p['combined_name'])

    logger.matching_tracks(len(p['dj_md_contents']))
    tracks = []

    for content in p['dj_md_contents']:
        file_name = content['file_name_l']
        folder_path = content['folder_path']
        title = content['title']

        # FAST LOOKUP - No Plex search needed!
        track = track_map['by_filename'].get(file_name)
        if not track and title:
            track = track_map['by_title'].get(title.lower())

        if track:
            tracks.append(track)
        else:
            # FolderPath already includes the file name in the rekordbox DB
            full_path = folder_path or file_name
            not_found_tracks.append(
                {
                    'playlist': combined_title,
                    'file_name': file_name,
                    'full_path': full_path,
                    'title': title,
                }
            )

    # Show not found tracks for this playlist
    playlist_not_found = [
        nf for nf in not_found_tracks if nf['playlist'] == combined_title
    ]
    if playlist_not_found:
        for nf in playlist_not_found:
            logger.track_not_found(nf['file_name'], nf['title'], nf['full_path'])

    # Get current track IDs
    rekordbox_track_ids = [track.ratingKey for track in tracks]

    # Check if playlist exists and needs updating
    if combined_title in playlist_map:
        existing_playlist_data = playlist_map[combined_title]
        existing_playlist = existing_playlist_data['playlist']
        existing_track_ids = existing_playlist_data['track_ids']

        # Check if playlist is smart (can't modify smart playlists)
        if existing_playlist.smart:
            logger.skipping_plex_smart_playlist(combined_title)
            smart_playlists_skipped.append(combined_title)
            continue

        # Compare playlists, they are only skipped if they're truly identical
        if rekordbox_track_ids == existing_track_ids:
            logger.playlist_up_to_date(combined_title, len(tracks))
            skipped_playlists.append(
                {'name': combined_title, 'tracks': len(tracks), 'reason': 'Up to date'}
            )
            continue
        else:
            logger.playlist_updating(
                combined_title, len(existing_track_ids), len(tracks)
            )

            # Remove all tracks and re-add (batch operation for efficiency)
            try:
                items_to_remove = existing_playlist.items()
                if items_to_remove:
                    existing_playlist.removeItems(items_to_remove)
            except Exception as e:
                logger.playlist_update_error(combined_title, e)

            existing_playlist.addItems(tracks)
            updated_playlists.append(
                {
                    'name': combined_title,
                    'old_tracks': len(existing_track_ids),
                    'new_tracks': len(tracks),
                    'added': len(tracks) - len(existing_track_ids),
                }
            )
            logger.playlist_updated(combined_title)
    else:
        if not tracks:
            logger.no_tracks_in_playlist(combined_title)
            skipped_playlists.append(
                {'name': combined_title, 'reason': 'No matching tracks'}
            )
            continue
        logger.creating_playlist(combined_title, len(tracks))
        plex.createPlaylist(title=combined_title, items=tracks)
        created_playlists.append({'name': combined_title, 'tracks': len(tracks)})
        logger.playlist_created(combined_title)

# Export not-found tracks to file
if not_found_tracks:
    with open('not-found.json', 'w') as f:
        json.dump(not_found_tracks, f, indent=2)

# Print summary
has_changes = created_playlists or updated_playlists or smart_playlists_skipped

if not has_changes:
    logger.all_in_sync_header()
    if not_found_tracks:
        logger.not_found_tracks_exported(len(not_found_tracks))
    logger.section_footer()
else:
    logger.sync_summary_header()

    logger.created_playlists_summary(created_playlists)
    logger.updated_playlists_summary(updated_playlists)
    logger.skipped_smart_playlists_summary(smart_playlists_skipped)

    total_processed = (
        len(created_playlists)
        + len(updated_playlists)
        + len(skipped_playlists)
        + len(smart_playlists_skipped)
    )
    logger.sync_complete(total_processed)
    if not_found_tracks:
        logger.not_found_tracks_exported(len(not_found_tracks))
    logger.section_footer()
