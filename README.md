# <img src='/images/usbmusic.png' card_color='#40DBB0' width='50' height='50' style='vertical-align:bottom'/> USB Music
Play Music from a USB device with Mycroft.ai

## About 
Play local music by inserting a USB drive into your Mycroft device. Upon Inserting a USB Device Mycroft
will scan the device for MP3 music and add it to a temporary library that you can play. 
## AutoPlay
If autoplay is enabled in the websettings then the usb music will begin playing imediatly when inserted.
Unplugging the usb will automatically stop and unmount the device.
# <img src='/images/settings.png' card_color='#40DBB0' width='355' height='190' style='vertical-align:bottom'/>
## Command Examples
* "play the artist elvis Presley"
* "play all shook up"
* "play the song blue suede shoes"
* "play the album appeal to reason"

## Credits 
* PCWii (20200709 Covid-19 Project)
* Some elements borrowed from https://github.com/Preston-Sundar/RaspberryPi-Pyudev-Usb-Storage-Detector/blob/master/usbdev.py
## Category
**Media**
## Tags
'#music, #usb, #mycroft.ai, #python, #skills, #mp3, #CPS'
## Require 
Tested on platform_picroft (others untested) 
## Other Requirements
- [Mycroft](https://docs.mycroft.ai/installing.and.running/installation)
- [mutagen](https://mutagen.readthedocs.io/en/latest/)
- [pyudev](https://pyudev.readthedocs.io/en/latest/)
## Installation Notes
- SSH and run: <b>msm install https://github.com/pcwii/usb-music.git</b>
## Todo
- Add "next/previous" commands
- Add "random" selection
- Add thumbnails for display
- ...?