# <img src='/images/usbmusic.png' card_color='#40DBB0' width='50' height='50' style='vertical-align:bottom'/> USB Music
Play Music from local (non-cloud based) sources (usb, smb, local path) with Mycroft.ai

## About 
This Skill will play local (non-cloud) music sources (USB, SMB, Local)
1. Inserting a USB drive into your Mycroft device. Upon Inserting a USB Device Mycroft
will scan the device for playable music and add it to a temporary library that you can play.
2. Adding an SMB source will let you play music from that source.
3. Adding a local path source will let you play music from that source.
4. Supports the following music formats 'mp3', 'm4a', 'flac', 'wav', 'wma','aac' 
# Features
## AutoPlay
If AutoPlay is enabled in the websettings then the USB music will begin playing immediately when inserted.
Unplugging the usb will automatically stop and unmount the USB device.
AutoPlay only functions with USB sources, not SMB or Local Path.
# <img src='/images/settings.png' card_color='#40DBB0' width='355' height='190' style='vertical-align:bottom'/>
## Automatic Insert Command Request
If enabled the skill will automatically send a command to the messagebus
when the USB is inserted.
Why? 
Why not?
This will let you do all sorts of things with this skill by invoking other skills.
Example:
- You have a running playlist that is stored on a USB stick.
- You insert the USB before you jump on the treadmill.
- The insertion automatically issues the following command to the messagebus
- "set a timer for 20 minutes"
- Now you have workout music and a timer to notify you when your workout is complete. 

## Command Examples - 
###Collecting the library may take several minutes depending on the library size
* "play the artist elvis Presley"
* "play all shook up"
* "play the song blue suede shoes"
* "play the album appeal to reason"
* "play music by Elton John"
* "play my music"
* "play some music"
* "play any music"
* "update network library"
* "update local library"
* "update usb library"
* "update music library"
* "stop"

## Credits 
* PCWii (20200709 Covid-19 Project)
* Some elements borrowed from https://github.com/Preston-Sundar/RaspberryPi-Pyudev-Usb-Storage-Detector/blob/master/usbdev.py
## Category
**Media**
## Tags
'#music, #usb, #mycroft.ai, #python, #skills, #mp3, #m4a, #flac, #wav, #wma, #aac, #CPS, #SMB, #Local '
## Require 
Tested on platform_picroft (others untested) 
## Other Requirements
- [Mycroft](https://docs.mycroft.ai/installing.and.running/installation)
- [mutagen](https://mutagen.readthedocs.io/en/latest/)
- [pyudev](https://pyudev.readthedocs.io/en/latest/)
- [vlc](https://www.videolan.org/index.html)
## Installation Notes
- SSH and run: <b>msm install https://github.com/pcwii/usb-music.git</b>
## Todo
- Add "next/previous" commands
- Add "random" selection
- Add thumbnails for display
- Need to cleanup the regex and make requests more generic (20210508)
- ~~Add Network "SMB" support (20200710)~~
- ~~Add support for other music formats (FLAC, OGG)~~
- ~~Add Local path support (20200722)~~