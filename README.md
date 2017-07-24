# Drosh
Script to upload Shutter screenshots to Dropbox and show a notification with the shared link created.

![Example](https://www.dropbox.com/s/2vz4xuksyoaqu4a/screencast.gif?dl=0&raw=true)

# Requirements

- inotify
- dropbox
- Something to daemonize the script

# Setup

## Create Dropbox App

Create a Dropbox App in https://www.dropbox.com/developers/apps with *full access* then in the OAuth2 section create your private access token and configure the script.

## Quick start
```
pip install -r requirements.txt

export DROSH_DROPBOX_TOKEN='<your-dropbox-token>'
export DROSH_DROPBOX_FOLDER='<your-dropbox-screehshots-folder>'
export DROSH_SCREENSHOT_FOLDER='<your-system-screenshot-folder>'
(env) python drosh.py
```

## Setup with supervisor

### Environment variables
```
DROSH_DROPBOX_TOKEN - OAuth2 token generated in the Dropbox App
DROSH_DROPBOX_FOLDER - Web site Dropbox folder
DROSH_SCREENSHOT_FOLDER - Full path to your Dropbox folder where you save screenshots
USER - Your username
HOME - Your home path
LOGNAME - Your username
DISPLAY - Your X Server screen, ":0.0" by default. https://askubuntu.com/questions/432255/what-is-display-environment-variable  
```


### Supervisor script
```
[program:drosh]
command=<full-path-virtualenv>/bin/python <path-to-drosh>/drosh.py
user=<your-username>
autostart=true
autorestart=true
stderr_logfile=/var/log/drosh-stderr.log
stdout_logfile=/var/log/drosh-std.log
environment=DROSH_DROPBOX_TOKEN='<your-dropbox-token>',DROSH_DROPBOX_FOLDER='<your-dropbox-screehshots-folder>',DROSH_SCREENSHOT_FOLDER='<your-system-screenshot-folder>',USER=<your-username>,HOME=<your-home-folder>,LOGNAME=<your-username>,DISPLAY=":0.0"
```
