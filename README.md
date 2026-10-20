# rekordbox-plexamp-sync

CLI to sync rekordbox playlists over to plexamp

<p float="left">
  <img src="./rekordbox.png" width="350" />
  <img src="./plexamp.png" width="350" />
</p>


## How it works
This tool will extract all playlists from the rekordbox database, then interact with the Plex Media Server API to create new playlists for each one. 

**Note:** This will only work if your rekordbox library is indexed by Plex. Make sure you deactivate all content matchers for Albums so that Plex does not match and rename tracks. This messes with the track matching to rekordbox, the titles need to be identical for better results

## Usage (mac)

Get your Plex token and server url. You can get the Plex token from localstorage when connecting to your server through the browser.

```python
virtualenv venv
pip install -r requirements.txt

# Build library
make

# Requires Python 3.8+
python app.py <server url> <token> [--verbose|-v]
```

Example: `python app.py 'http://localhost:32400' '123456abcdefg' --verbose`

The server URL and token can also come from the `PLEX_URL` and `PLEX_TOKEN` environment variables, in which case both arguments can be omitted.

## Plex behind a reverse proxy or Cloudflare Access

Send extra HTTP headers with every Plex request using `-H`/`--header` (repeatable):

```sh
python app.py <server url> <token> -H 'X-Custom-Auth: secret'
```

For a server protected by [Cloudflare Access](https://developers.cloudflare.com/cloudflare-one/applications/), create a [service token](https://developers.cloudflare.com/cloudflare-one/identity/service-tokens/), add a policy with the **Service Auth** action that includes the token to the Access application, and export its credentials:

```sh
export PLEX_URL='https://plex.example.com'
export PLEX_TOKEN='123456abcdefg'
export CF_ACCESS_CLIENT_ID='<client id>.access'
export CF_ACCESS_CLIENT_SECRET='<client secret>'
python app.py
```

When both `CF_ACCESS_CLIENT_ID` and `CF_ACCESS_CLIENT_SECRET` are set, the `CF-Access-Client-Id` and `CF-Access-Client-Secret` headers are added to every request. Without them, Access redirects the script to its login page.

## Usage (windows)
I don't have a windows machine to try this on, but build the shared library with Golang.

Edit `main.go` and change the rekordbox pathes. Check the [go-rekordbox README](https://github.com/dvcrn/go-rekordbox#usage) about where to find these pathes:

```go
	optionsFilePath := filepath.Join(homeDir, "/Library/Application Support/Pioneer/rekordboxAgent/storage/", "options.json")

	// Files and paths
	asarPath := "/Applications/rekordbox 6/rekordbox.app/Contents/MacOS/rekordboxAgent.app/Contents/Resources/app.asar"
```

Then build the shared lib and generate a dll

```
go build -buildmode=c-shared -o library.dll main.go
```

Update `app.py` `get_playlists()` to load the new dll instead:

```go
library = ctypes.cdll.LoadLibrary('./library.dll')
```

Then, follow steps from "Usage (mac)"

## Limitations and todos
- Intelligent Playlists aren't supported yet, this needs some extra work
- Matching happens against filename and then title as backup, this can still be improved

## Acknowledgements
This CLI is powered by my [go-rekordbox](https://github.com/dvcrn/go-rekordbox) SDK to interact with the rekordbox DB, and [python-plexapi](https://github.com/pkkid/python-plexapi) to interact with Plex
