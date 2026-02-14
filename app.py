import ctypes
import json
import sys
from typing import Any, Dict, List, TypedDict, Union

from plexapi.server import PlexServer
from tqdm import tqdm


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


def build_plex_track_map(plex: PlexServer) -> Dict[str, Any]:
    """Build maps of all tracks in Plex for fast lookups"""
    print('🗺️  Building Plex track map...')

    track_map = {'by_filename': {}, 'by_title': {}}

    # Get all music sections/libraries
    for section in plex.library.sections():
        if section.type == 'artist':  # Music library
            print(f'   Indexing library: {section.title}')
            tracks = section.searchTracks()

            for track in tqdm(
                tracks, desc=f'   Indexing {section.title}', unit=' tracks', leave=False
            ):
                # Map by filename
                if hasattr(track, 'media') and track.media:
                    for media in track.media:
                        for part in media.parts:
                            filename = (
                                part.file.split('/')[-1]
                                if '/' in part.file
                                else part.file.split('\\')[-1]
                            )
                            track_map['by_filename'][filename] = track

                # Map by title (lowercase for better matching)
                if track.title:
                    track_map['by_title'][track.title.lower()] = track

    print(f'✓ Indexed {len(track_map["by_filename"])} tracks by filename')
    print(f'✓ Indexed {len(track_map["by_title"])} tracks by title\n')

    return track_map


def build_plex_playlist_map(plex: PlexServer) -> Dict[str, Dict]:
    """Build a map of existing Plex playlists with their track IDs"""
    print('📋 Building Plex playlist map...')

    playlist_map = {}
    playlists = plex.playlists()

    for playlist in tqdm(playlists, desc='   Indexing playlists', unit=' playlists'):
        if playlist.smart:
            continue  # Skip smart playlists

        track_ids = set(track.ratingKey for track in playlist.items())
        playlist_map[playlist.title] = {'playlist': playlist, 'track_ids': track_ids}

    print(f'✓ Found {len(playlist_map)} existing playlists\n')
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


pl = get_playlists()


if len(sys.argv) <= 2:
    print('Please provide a valid URL and token')
    print('Usage: python3 app.py <server url> <token>')
    sys.exit(0)

token = sys.argv[2]
server_url = sys.argv[1]

plex = PlexServer(server_url, token)

# Build maps ONCE at the start
track_map = build_plex_track_map(plex)
playlist_map = build_plex_playlist_map(plex)

print(f'\nFound {len(pl)} Rekordbox playlists to sync\n')

# Track changes for summary
created_playlists = []
updated_playlists = []
skipped_playlists = []
smart_playlists_skipped = []
not_found_tracks = []  # Track not found tracks for export

for p in tqdm(pl, desc='Syncing playlists', unit='playlist'):
    playlist_title = p['dj_md_playlist']['name']

    # Skip smart playlists
    smart_list_data = p['dj_md_playlist'].get('smart_list')
    if smart_list_data and smart_list_data != '':
        tqdm.write(f'⏭️  Skipping smart playlist: {playlist_title}')
        smart_playlists_skipped.append(playlist_title)
        continue

    tqdm.write(f'📝 Processing: {playlist_title}')

    if 'dj_md_contents' not in p or len(p['dj_md_contents']) == 0:
        combined_title = '{}'.format(p['combined_name'])
        tqdm.write(f'⚠️  No tracks in playlist: {playlist_title}')
        skipped_playlists.append({'name': combined_title, 'reason': 'No tracks'})
        continue

    combined_title = '{}'.format(p['combined_name'])

    tqdm.write(f'🎵 Matching {len(p["dj_md_contents"])} tracks...')
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
            full_path = f'{folder_path}/{file_name}' if folder_path else file_name
            not_found_tracks.append(
                {
                    'playlist': combined_title,
                    'file_name': file_name,
                    'full_path': full_path,
                    'title': title,
                }
            )

    # Show not found tracks for this playlist (filenames only)
    playlist_not_found = [
        nf for nf in not_found_tracks if nf['playlist'] == combined_title
    ]
    if playlist_not_found:
        for nf in playlist_not_found:
            tqdm.write(f'  ⚠️  Track not found: {nf["file_name"]}')

    # Get current track IDs
    rekordbox_track_ids = set(track.ratingKey for track in tracks)

    # Check if playlist exists and needs updating
    if combined_title in playlist_map:
        existing_playlist_data = playlist_map[combined_title]
        existing_playlist = existing_playlist_data['playlist']
        existing_track_ids = existing_playlist_data['track_ids']

        # Check if playlist is smart (can't modify smart playlists)
        if existing_playlist.smart:
            tqdm.write(
                f"⏭️  Skipping - existing Plex playlist '{combined_title}' is a smart playlist"
            )
            smart_playlists_skipped.append(combined_title)
            continue

        # Compare track sets
        if rekordbox_track_ids == existing_track_ids:
            tqdm.write(
                f'✓ Playlist "{combined_title}" is already up to date ({len(tracks)} tracks), skipping\n'
            )
            skipped_playlists.append(
                {'name': combined_title, 'tracks': len(tracks), 'reason': 'Up to date'}
            )
            continue
        else:
            tqdm.write(
                f'🔄 Playlist has changed, updating... (was {len(existing_track_ids)}, now {len(tracks)} tracks)'
            )

            # Remove all tracks and re-add
            for track in existing_playlist.items():
                try:
                    existing_playlist.removeItems([track])
                except:
                    pass

            existing_playlist.addItems(tracks)
            updated_playlists.append(
                {
                    'name': combined_title,
                    'old_tracks': len(existing_track_ids),
                    'new_tracks': len(tracks),
                    'added': len(tracks) - len(existing_track_ids),
                }
            )
            tqdm.write(f'✅ Updated playlist: {combined_title}\n')
    else:
        tqdm.write(
            f'💾 Creating new playlist: {combined_title} ({len(tracks)} tracks)...'
        )
        plex.createPlaylist(title=combined_title, items=tracks)
        created_playlists.append({'name': combined_title, 'tracks': len(tracks)})
        tqdm.write(f'✅ Created playlist: {combined_title}\n')

# Export not-found tracks to file
if not_found_tracks:
    with open('not-found.json', 'w') as f:
        json.dump(not_found_tracks, f, indent=2)

# Print summary
has_changes = created_playlists or updated_playlists or smart_playlists_skipped

if not has_changes:
    print('\n' + '=' * 70)
    print('✅ Everything is already in sync!')
    print('=' * 70)
    if not_found_tracks:
        print(f'\n⚠️  {len(not_found_tracks)} track(s) not found in Plex')
        print(f'📄 Details exported to: not-found.json')
    print('=' * 70 + '\n')
else:
    print('\n' + '=' * 70)
    print('📊 SYNC SUMMARY')
    print('=' * 70)

    if created_playlists:
        print(f'\n✨ Created {len(created_playlists)} playlist(s):')
        for pl in created_playlists:
            print(f'   • {pl["name"]} ({pl["tracks"]} tracks)')

    if updated_playlists:
        print(f'\n🔄 Updated {len(updated_playlists)} playlist(s):')
        for pl in updated_playlists:
            change = f'+{pl["added"]}' if pl['added'] > 0 else str(pl['added'])
            print(
                f'   • {pl["name"]} ({pl["old_tracks"]} → {pl["new_tracks"]} tracks, {change})'
            )

    if smart_playlists_skipped:
        print(f'\n🔒 Skipped {len(smart_playlists_skipped)} smart playlist(s):')
        for name in smart_playlists_skipped:
            print(f'   • {name}')

    total_processed = (
        len(created_playlists)
        + len(updated_playlists)
        + len(skipped_playlists)
        + len(smart_playlists_skipped)
    )
    print(f'\n{"=" * 70}')
    print(f'Total: {total_processed} playlists processed')
    print('🎉 Sync complete!')
    if not_found_tracks:
        print(f'\n⚠️  {len(not_found_tracks)} track(s) not found in Plex')
        print(f'📄 Details exported to: not-found.json')
    print('=' * 70 + '\n')
