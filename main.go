package main

import (
	"context"
	"fmt"
	"os"
	"path/filepath"

	"C"

	"github.com/dvcrn/go-rekordbox/rekordbox"
)
import "encoding/json"

type Playlist struct {
	CombinedName string                   `json:"combined_name"`
	DJMdPlaylist *rekordbox.DjmdPlaylist  `json:"dj_md_playlist,omitempty"`
	DJMdContents []*rekordbox.DjmdContent `json:"dj_md_contents,omitempty"`
}

func getRecursivePlaylistName(ctx context.Context, client *rekordbox.Client, playlist *rekordbox.DjmdPlaylist, nameSoFar string) string {
	// check if has a parent
	if playlist.ParentID.String() == "root" {
		return nameSoFar
	}

	// get parent
	parent, err := client.DjmdPlaylistByID(ctx, playlist.ParentID)
	if err != nil {
		panic(err)
	}

	name := fmt.Sprintf("%s - %s", parent.Name.String(), nameSoFar)
	return getRecursivePlaylistName(ctx, client, parent, name)
}

//export getPlaylists
func getPlaylists() *C.char {
	ctx := context.Background()

	homeDir, err := os.UserHomeDir()
	if err != nil {
		panic(err)
	}

	optionsFilePath := filepath.Join(homeDir, "/Library/Application Support/Pioneer/rekordboxAgent/storage/", "options.json")

	// Files and paths
	asarPath := "/Applications/rekordbox 6/rekordbox.app/Contents/MacOS/rekordboxAgent.app/Contents/Resources/app.asar"

	client, err := rekordbox.NewClient(optionsFilePath, asarPath)
	if err != nil {
		panic(err)
	}

	defer client.Close()

	playlists, err := client.AllDjmdPlaylist(ctx)
	if err != nil {
		panic(err)
	}

	parsedPlaylists := []*Playlist{}
	for _, playlist := range playlists {
		pl := &Playlist{}

		playlistSongs, err := client.DjmdSongPlaylistByPlaylistID(ctx, playlist.ID)
		if err != nil {
			panic(err)
		}

		if len(playlistSongs) == 0 {
			continue
		}

		pl.DJMdPlaylist = playlist
		pl.CombinedName = getRecursivePlaylistName(ctx, client, playlist, playlist.Name.String())

		for _, playlistSong := range playlistSongs {
			content, err := client.DjmdContentByID(ctx, playlistSong.ContentID)
			if err != nil {
				panic(err)
			}

			pl.DJMdContents = append(pl.DJMdContents, content)
		}

		parsedPlaylists = append(parsedPlaylists, pl)
	}

	// marshal playlists to json
	b, err := json.Marshal(parsedPlaylists)
	if err != nil {
		panic(err)
	}

	return C.CString(string(b))
}

func main() {
}
