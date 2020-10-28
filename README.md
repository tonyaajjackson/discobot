# discobot
Collects songs posted in your Discord server into playlists!

[![forthebadge made-with-python](http://ForTheBadge.com/images/badges/made-with-python.svg)](https://www.python.org/)

discobot is a Discord chat bot that monitors a channel in a Discord server for Spotify links to build "Recent" and "All Time" playlists on Spotify.

If there's a Spotify link in a message, the bot will immediately add any new song(s) from the link to the "All Time" playlist as well as a "Buffer" playlist. Songs that are already on a playlist are not re-added.

Specifically, if the Spotify link is a track, the track will be added. If it's an album, all songs on the album will be added. If it's an artist, the artist's top 10 songs will be added. All other link types such as playlist, user, podcast episode, etc. are ignored.

On a configurably regular basis, the bot will:
    
1. Wipe the "Recent" playlist
1. Copy all songs from the "Buffer" playlist to the "Recent" playlist
1. Wipe the "Buffer" playlist
1. Send Discord messages in the specified channel to let members know that the new Recent playlist is available
1. Send a Discord message to remind people of the "All Time" playlist


## Setup
### Python Environment
1.  Install [pyenv](https://github.com/pyenv/pyenv)
1.  Install pipenv:

    `pip install pipenv`

1. Set up virtual environment:

    `pipenv install`

1. Rename `/template_config.json` to `/config.json`

### Discord

1. Create a Discord bot and connect it to your server by following Discord's tutorial [here](https://discordpy.readthedocs.io/en/latest/discord.html). Make sure the following settings are set:
    * Public bot = false
    * Requires OAUTH2 GRANT = false

1. Copy the bot token into the discord `token` field in `config.json`.

1. Enable Discord developer mode by following the tutorial [here](https://discordia.me/en/developer-mode).

1. In discord, right click the channel you want to monitor and select "Copy ID", then paste the channel id into the discord `channel_id` field in `config.json` (without quotes)

1. Add the bot to your discord server by following the tutorial [here](https://discordpy.readthedocs.io/en/latest/discord.html#inviting-your-bot). The bot requires these permissions:
    * Send Messages
    * Manage Messages


### Spotify
1. Create a Spotify app by following their tutorial [here](https://developer.spotify.com/documentation/general/guides/app-settings/#register-your-app)

1. Copy the app's Client ID and Client Secret to the spotipy `client_id` and `secret` fields in `config.json`

1. Click "Edit Settings" in the Spotify dashboard, then under "Redirect URIs" fill in "ht<span>tps://localhost/"

1. In Spotify, create the following three playlists:
    1. An "All Time" playlist
    1. A "Recent" playlist
    1. A "Buffer" playlist
    
    You can adjust the names of the playlists as desired, e.g. "Music Chat All Time", so long as there are three playlists

1. (Optional) Right click on the "Buffer" playlist in Spotify and click "Make Secret"

1. Right click on each playlist and click "Share"->"Copy Spotify URI". Paste each playlist's URI into the corresponding field under spotipy in `config.json`

### "Recent" Playlist Refresh Scheduling

1. Create a cron expression for when and how often the bot will refresh the "Recent" playlist. For example, the cron expression for refreshing once a week at 6:00 PM on Saturday is:

    `0 18 * * 6`

    You can use [crontab.guru](https://crontab.guru/#0_18_*_*_6) to build the cron expression

1. Copy the cron expression into the `playlist_update_cron_expr` field in `config.json`


## Usage
### Command Line
1. To activate the python virtual environment, run:
    
    `pipenv shell`

1. The chat bot can then be started with:

    `python discobot.py`

1. If a valid Spotify Oauth .cache file is not present, you will be prompted to visit a Spotify link to authorize the chat bot to connect to your spotify account
    * Authorizing the bot will redirect you to a link like ht<span>tps://localhost/?code=\<authorization code here\>.
    * Note: seeing an "unable to connect" or "site can't be reached" error is normal - the URL with code should be in the browser's address bar

1. Copy the URL you are redirected to and paste it into prompt in the command line

### Docker
Running the chat bot in a Docker container requires a valid .cache file that will be copied into the Docker container.

1. Start the chat bot once from the command line and complete the Spotify OAuth authorization process to create a valid .cache file
1. Build the Docker container. This will also copy the .cache file into the Docker container
    
    `docker build . --tag discobot`

1. Run the docker container

    `docker run discobot:latest`
