
# Mopidy skill for Snips

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](https://raw.githubusercontent.com/snipsco/snips-skill-hue/master/LICENSE.txt)

Kudos to [tschmidty69](https://github.com/tschmidty69) for his initial contribution.

## Requirements

You will need to install in a computer and configure:

 - [Mopidy](http://musicpartners.Mopidy.com/docs?q=node/442)
 - [Spotify Mopidy extension](https://github.com/mopidy/mopidy-spotify)

Find here how to set it up.

**Install Mopidy**

~~~shell
wget -q -O - https://apt.mopidy.com/mopidy.gpg | sudo apt-key add -
sudo wget -q -O /etc/apt/sources.list.d/mopidy.list https://apt.mopidy.com/jessie.list
sudo apt-get update
sudo apt-get install mopidy
~~~

[Install Spotify extension](https://github.com/mopidy/mopidy-spotify) to be able to play spotify content
~~~
sudo apt-get install mopidy-spotify
~~~

Run `mopidy config`, this will show you the default config file used by mopdidy. Alos, on it is first run it will create a user config file that you can use to update the default one. The user config file is found under the following path `~/.config/mopidy/mopidy.conf` in your Raspberry Pi.

Run `nano ~/.config/mopidy/mopidy.conf`. The following values should be uncommented and overwritten with what is given here:
~~~
[audio]
mixer_volume = 100
mixer = software
output = alsasink

[local]
enabled = false

[spotify]
username = YOUR_USERAME
password = YOUR_PASSWORD
client_id = YOUR_CLIENT_ID
client_secret = YOUR_CLIENT_SECRET
~~~

In order to get a Spotify client Id and client secret you need to:

- [Create a Spotify application](https://developer.spotify.com/my-applications/)
- Retrieve the `client_id` and the `client_secret` from the application

Finally, run Mopidy in the terminal

~~~
mopidy
~~~

If everything is fine you should not see any errors on the logs.

## Snips Skills Manager

It is recommended that you use this skill with the [Snips Skills Manager](https://github.com/snipsco/snipsskills). Simply add the following section to your [Snipsfile](https://github.com/snipsco/snipsskills/wiki/The-Snipsfile) :

~~~yaml
skills:
  - pip: https://github.com/snipsco/snips-skill-mopidy
    package_name: snipsmopidy
    params:
      mopidy_host: <YOUR_IP> # defaults to localhost
      spotify_refresh_token: <YOUR_SPOTIFY_REFRESH_TOKEN>
      spotify_client_id: <YOUR_SPOTIFY_CLIENT_ID>
      spotify_client_secret: <YOUR_SPOTIFY_CLIENT_SECRET>
~~~

## Usage

The skill allows you to control [Mopidy](http://musicpartners.Mopidy.com/docs?q=node/442) running in a computer like a Raspberry Pi. You can use it as follows:

~~~python
from snipsmopidy.snipsmopidy import SnipsMopidy

Mopidy = SnipsMopidy(<SPOTIFY_REFRESH_TOKEN>, <SPOTIFY_CLIENT_ID>, <SPOTIFY_CLIENT_SECRET>)
Mopidy.play_artist("John Coltrane")
~~~

The `SPOTIFY_REFRESH_TOKEN` is used for playing music from Spotify. You can obtain it from the [Snips Spotify Login](https://snips-spotify-login.herokuapp.com) page.

## Copyright

This skill is provided by [Snips](https://www.snips.ai) as Open Source software. See [LICENSE.txt](https://github.com/snipsco/snips-skill-hue/blob/master/LICENSE.txt) for more
information.
