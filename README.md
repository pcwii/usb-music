# <img src='https://raw.githack.com/FortAwesome/Font-Awesome/master/svgs/solid/music.svg' card_color='#40DBB0' width='50' height='50' style='vertical-align:bottom'/> USB Music
Play Music from a USB device with Mycroft.ai

## About 
Play local music by inserting a USB drive into your Mycroft device. Upon Inserting a USB Device Mycroft
will scan the device for MP3 music and add it to a temporary library that you can play by asking. 
####Supports CPS
## Examples
###Music
* "play the artist elvis Presley"
* "play all shook up"
* "play the song blue suede shoes"
* "play the album appeal to reason"

## Credits 
* PCWii (20200526 Covid-19 Project)
* Original work forked from https://github.com/Cadair/mycroft-kodi
* Some elements borrowed from https://github.com/Preston-Sundar/RaspberryPi-Pyudev-Usb-Storage-Detector/blob/master/usbdev.py
## Category
**Media**
## Tags
'#music, #usb, #mycroft.ai, #python, #skills, #mp3'
## Require 
Tested on platform_picroft (others untested) 
## Other Requirements
- [Mycroft](https://docs.mycroft.ai/installing.and.running/installation)
- [mutagen](https://mutagen.readthedocs.io/en/latest/)
- [pyudev](https://pyudev.readthedocs.io/en/latest/)
## Installation Notes
- SSH and run: msm install https://github.com/pcwii/usb-music.git
## Todo
- Add USB Polling interval to Mycroft.ai web interface (currently 1 second)