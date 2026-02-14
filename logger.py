from typing import Any, Dict, List

from tqdm import tqdm as tqdm_base


class Logger:
    """Configurable logger for controlling output verbosity"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def info(self, message: str):
        """Print general info messages"""
        if self.verbose:
            print(message)

    def simple(self, message: str):
        """Print simple messages (always shown, for non-verbose fallback)"""
        print(message)

    def tqdm_write(self, message: str):
        """Write messages within tqdm loops"""
        if self.verbose:
            tqdm_base.write(message)

    def tqdm(self, iterable, **kwargs):
        """Create a tqdm progress bar that respects verbose setting"""
        kwargs['disable'] = not self.verbose
        return tqdm_base(iterable, **kwargs)

    def section_header(self, title: str):
        """Print a section header with separators"""
        if self.verbose:
            print('\n' + '=' * 70)
            print(title)
            print('=' * 70)

    def section_footer(self, message: str = ''):
        """Print a section footer"""
        if self.verbose:
            if message:
                print(message)
            print('=' * 70 + '\n')

    # Semantic logging methods for specific actions

    def building_track_map(self):
        """Log start of track map building"""
        self.info('🗺️  Building Plex track map...')

    def indexing_library(self, library_name: str):
        """Log indexing of a specific library"""
        self.info(f'   Indexing library: {library_name}')

    def track_map_complete(self, filename_count: int, title_count: int):
        """Log completion of track map building"""
        self.info(f'✓ Indexed {filename_count} tracks by filename')
        self.info(f'✓ Indexed {title_count} tracks by title\n')

    def building_playlist_map(self):
        """Log start of playlist map building"""
        self.info('📋 Building Plex playlist map...')

    def playlist_map_complete(self, count: int):
        """Log completion of playlist map building"""
        self.info(f'✓ Found {count} existing playlists\n')

    def rekordbox_playlists_found(self, count: int):
        """Log number of Rekordbox playlists found"""
        self.info(f'\nFound {count} Rekordbox playlists to sync\n')

    def skipping_smart_playlist(self, name: str):
        """Log skipping of a smart playlist"""
        self.tqdm_write(f'⏭️  Skipping smart playlist: {name}')

    def processing_playlist(self, name: str):
        """Log start of playlist processing"""
        if self.verbose:
            self.tqdm_write(f'📝 Processing: {name}')
        else:
            self.simple(f'syncing {name}')

    def no_tracks_in_playlist(self, name: str):
        """Log warning about empty playlist"""
        if self.verbose:
            self.tqdm_write(f'⚠️  No tracks in playlist: {name}')
        else:
            self.simple(f'no tracks in playlist {name}')

    def matching_tracks(self, count: int):
        """Log start of track matching"""
        self.tqdm_write(f'🎵 Matching {count} tracks...')

    def track_not_found(self, filename: str, title: str = '', folder_path: str = ''):
        """Log a track that wasn't found"""
        if self.verbose:
            self.tqdm_write(f'  ⚠️  Track not found: {filename}')
        else:
            self.simple(f'track not found {title} {folder_path}')

    def playlist_up_to_date(self, name: str, track_count: int):
        """Log that a playlist is already up to date"""
        self.tqdm_write(
            f'✓ Playlist "{name}" is already up to date ({track_count} tracks), skipping\n'
        )

    def playlist_updating(self, name: str, old_count: int, new_count: int):
        """Log that a playlist is being updated"""
        self.tqdm_write(
            f'🔄 Playlist has changed, updating... (was {old_count}, now {new_count} tracks)'
        )

    def playlist_update_error(self, name: str, error: Exception):
        """Log error during playlist update"""
        self.tqdm_write(f'  ⚠️  Could not remove items from playlist {name}: {error}')

    def playlist_updated(self, name: str):
        """Log successful playlist update"""
        if self.verbose:
            self.tqdm_write(f'✅ Updated playlist: {name}\n')
        else:
            self.simple(f'updated playlist {name}')

    def creating_playlist(self, name: str, track_count: int):
        """Log creation of new playlist"""
        self.tqdm_write(f'💾 Creating new playlist: {name} ({track_count} tracks)...')

    def playlist_created(self, name: str):
        """Log successful playlist creation"""
        if self.verbose:
            self.tqdm_write(f'✅ Created playlist: {name}\n')
        else:
            self.simple(f'created playlist {name}')

    def skipping_plex_smart_playlist(self, name: str):
        """Log skipping of existing Plex smart playlist"""
        self.tqdm_write(
            f"⏭️  Skipping - existing Plex playlist '{name}' is a smart playlist"
        )

    def not_found_tracks_exported(self, count: int):
        """Log that not-found tracks were exported"""
        self.info(f'\n⚠️  {count} track(s) not found in Plex')
        self.info('📄 Details exported to: not-found.json')

    def sync_summary_header(self):
        """Print sync summary header"""
        self.section_header('📊 SYNC SUMMARY')

    def all_in_sync_header(self):
        """Print header for when everything is in sync"""
        self.section_header('✅ Everything is already in sync!')

    def created_playlists_summary(self, playlists: List[Dict]):
        """Print summary of created playlists"""
        if not playlists:
            return
        self.info(f'\n✨ Created {len(playlists)} playlist(s):')
        for pl in playlists:
            self.info(f'   • {pl["name"]} ({pl["tracks"]} tracks)')

    def updated_playlists_summary(self, playlists: List[Dict]):
        """Print summary of updated playlists"""
        if not playlists:
            return
        self.info(f'\n🔄 Updated {len(playlists)} playlist(s):')
        for pl in playlists:
            change = f'+{pl["added"]}' if pl['added'] > 0 else str(pl['added'])
            self.info(
                f'   • {pl["name"]} ({pl["old_tracks"]} → {pl["new_tracks"]} tracks, {change})'
            )

    def skipped_smart_playlists_summary(self, playlist_names: List[str]):
        """Print summary of skipped smart playlists"""
        if not playlist_names:
            return
        self.info(f'\n🔒 Skipped {len(playlist_names)} smart playlist(s):')
        for name in playlist_names:
            self.info(f'   • {name}')

    def sync_complete(self, total_processed: int):
        """Print sync completion message"""
        self.info(f'\nTotal: {total_processed} playlists processed')
        self.info('🎉 Sync complete!')
