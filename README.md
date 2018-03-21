
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

We  will be running Mopidy as a service which which allow you to start it on boot and have control over it such as 
starting, stopping or restarting the service. First we have to change the config file that we can find under 
`/etc/mopidy/mopidy.conf` on your Raspberry Pi. The changes will update the default Mopidy config file. The following values should be added to the aforementioned file:

~~~
[audio]
mixer_volume = 100
mixer = software
output = alsasink

[local]
enabled = false

[spotify]
username = <SPOTIFY_USERNAME>
password = <SPOTIFY_PASSWORD>
client_id = <SPOTIFY_CLIENT_ID>
client_secret = <SPOTIFY_CLIENT_SECRET>
~~~

To enable music streaming and search from Spotify, you need a premium account and follow these steps:
- [Authenticate your Mopidy installation](https://www.mopidy.com/authenticate/#spotify) to access your Spotify account
- Retrieve the **client_id** and the **client_secret** from the application and use them to overwrite the values in the Mopidy config file. 

### Enable Mopidy as a Service
To enable Mopidy as a service please run the following:
~~~
(pi) $ sudo systemctl enable mopidy
~~~
Please now reboot your machine and ssh back to it:
~~~
(pi) $ sudo reboot
$ ssh pi@raspberrypi.local
~~~
Let’s take a look at the status and latest logs of Mopidy to ensure everything is running just fine
~~~
(pi) $ sudo systemctl status mopidy
~~~
If everything goes smoothly, you should not see any warnings or errors on the logs. If you do please ensure the values added on the config file are properly set.
You would also be able to manage the service as any other systemd service using the following commands:
~~~
(pi) $ sudo systemctl start mopidy 
(pi) $ sudo systemctl stop mopidy
(pi) $ sudo systemctl restart mopidy
~~~

## Snips Skills Manager

It is recommended that you use this skill with the [Snips Skills Manager](https://github.com/snipsco/snipsskills). Simply add the following section to your [Snipsfile](https://github.com/snipsco/snipsskills/wiki/The-Snipsfile) :

~~~yaml
skills:
  - pip: https://github.com/snipsco/snips-skill-mopidy
    package_name: snipsmopidy
    params:
      mopidy_host: <MOPIDY_IP> # defaults to localhost
      spotify_refresh_token: <SPOTIFY_REFRESH_TOKEN>
      spotify_client_id: <SPOTIFY_CLIENT_ID>
      spotify_client_secret: <SPOTIFY_CLIENT_SECRET>
~~~

## Usage

The skill allows you to control [Mopidy](http://musicpartners.Mopidy.com/docs?q=node/442) running in a computer like a Raspberry Pi. You can use it as follows:

~~~python
from snipsmopidy.snipsmopidy import SnipsMopidy

Mopidy = SnipsMopidy(SPOTIFY_REFRESH_TOKEN, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
Mopidy.play_artist("John Coltrane")
~~~

The `SPOTIFY_REFRESH_TOKEN` is used for playing music from Spotify. You can obtain it from the [Snips Spotify Login](https://snips-spotify-login.herokuapp.com) page.

## Copyright

This skill is provided by [Snips](https://www.snips.ai) as Open Source software. See [LICENSE.txt](https://github.com/snipsco/snips-skill-hue/blob/master/LICENSE.txt) for more
information.
