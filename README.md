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

    `mv ./cache/template_config.json ./cache/config.json`

1. Rename `/template_secrets.json` to `/secrets.json`

    `mv ./cache/template_secrets.json ./cache/secrets.json`

### Discord

1. Create a Discord bot and connect it to your server by following Discord's tutorial [here](https://discordpy.readthedocs.io/en/latest/discord.html). Make sure the following settings are set:
    * Public bot = false
    * Requires OAUTH2 GRANT = false

1. Copy the bot token into the discord `token` field in `secrets.json`.

1. Enable Discord developer mode by following the tutorial [here](https://discordia.me/en/developer-mode).

1. In Discord, right click the channel you want to monitor and select "Copy ID", then paste the channel id into the discord `monitoring_channel_ids` field in `config.json`. Repeat for each channel you wish to monitor for song links. For example:

    ```
    "monitoring_channel_ids": [
        12345,
        23456
    ]
    ```

1. In Discord, right click the channel you want send notifications to and select "Copy ID", then paste the channel id into the discord `notify_channel_id` field in `config.json`.

1. Add the bot to your discord server by following the tutorial [here](https://discordpy.readthedocs.io/en/latest/discord.html#inviting-your-bot). The bot requires these permissions:
    * Send Messages
    * Manage Messages


### Spotify
1. Create a Spotify app by following their tutorial [here](https://developer.spotify.com/documentation/general/guides/app-settings/#register-your-app)

1. Copy the app's Client ID and Client Secret to the spotipy `client_id` and `secret` fields in `secrets.json`

1. Click "Edit Settings" in the Spotify dashboard, then under "Redirect URIs" fill in "ht<span>tps://localhost/"

1. In Spotify, create the following three playlists:
    1. An "All Time" playlist
    1. A "Recent" playlist
    1. A "Buffer" playlist
    
    You can adjust the names of the playlists as desired, e.g. "Music Chat All Time", so long as there are three playlists

1. (Optional) Right click on the "Buffer" playlist in Spotify and click "Make Secret"

1. Right click on each playlist and click "Share"->"Copy Spotify URI". Paste each playlist's URI into the corresponding field under spotipy in `config.json`

### Adding Multiple Discord Servers (Guilds)
1. In `config.json`, copy the guild object in "guilds" and paste it below to create another guild. This example shows config.json with two guilds:

    ```
    "guilds": [
    {
      "_id": 12345,
      "monitoring_channel_ids": [
        12345
      ],
      "notify_channel_id": 12345,
      "all_time_playlist_uri": "spotify:playlist:<id>",
      "recent_playlist_uri": "spotify:playlist:<id>",
      "buffer_playlist_uri": "spotify:playlist:<id>",
      "is_connection_testing_guild": false,
      "testing_channel_id": 12345
    },
    {
      "_id": 54321,
      "monitoring_channel_ids": [
        54321
      ],
      "notify_channel_id": 54321,
      "all_time_playlist_uri": "spotify:playlist:<id>",
      "recent_playlist_uri": "spotify:playlist:<id>",
      "buffer_playlist_uri": "spotify:playlist:<id>",
      "is_connection_testing_guild": false,
      "testing_channel_id": 54321
    }
  ],
  ```

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
1. Create a config folder to store `config.json`, `secrets.json`, and the Spotify OAuth token between Docker container runs. For example:
    
    `mkdir -p /home/$USER/docker/discobot/config`

1. Copy `config.json` and `secrets.json` to the cache folder from step 1.

1. Build the Docker container
    
    `docker build . --tag discobot`

1. Run the docker container.

    `docker run -v <PATH_TO_DOCKER_CONFIG_FOLDER>:/discobot/config -it discobot:latest`

    The `-v` option connects the Spotify OAuth token folder to the container created in step 1. The `-it` option runs the container in interactive mode to allow the user to paste the Spotify OAuth redirect link into the terminal. If a valid Spotify OAuth .cache file exists 
