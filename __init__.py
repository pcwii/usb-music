from mycroft.skills.common_play_skill import CommonPlaySkill
from adapt.intent import IntentBuilder
from mycroft.skills.core import intent_handler, intent_file_handler
from mycroft.util.log import LOG

import threading

from .usbScan import usbdev

import time
import os
from os.path import dirname
from mutagen.easyid3 import EasyID3


class USBMusicSkill(CommonPlaySkill):
    class NewThread:
        id = 0
        idStop = False
        idThread = threading.Thread

    def __init__(self):
        super(USBMusicSkill, self).__init__('USBMusicSkill')
        self.song_list = []
        self.prev_status = False
        self.song_artist = ""
        self.song_title = ""
        self.song_album = ""
        self.prev_status = False
        self.status = False
        self.path = ""
        self.usb_monitor = self.NewThread
        LOG.info("USB Music Skill Loaded!")

    def initialize(self):
        self.load_data_files(dirname(__file__))
        LOG.info("USB Music Skill Initialized!")
        #self.usb_monitor.idStop = False
        #self.usb_monitor.id = 101
        #self.usb_monitor.idThread = threading.Thread(target=self.monitor_usb,
                                                     #args=(self.usb_monitor.id, lambda: self.usb_monitor.idStop))
        #self.usb_monitor.idThread.start()
        self.usb_monitor()

    def CPS_match_query_phrase(self, phrase):
        """
            The method is invoked by the PlayBackControlSkill.
        """
        LOG.info('USBMusicSkill received the following phrase: ' + phrase)
        if self.status:
            LOG.info("Searching for requested media...")
            # match_level = CPSMatchLevel.EXACT
            # playback_device = device_id
            # Todo add proper cps match level
            data = {
                "track": "my Movie Name"
            }
            #return (phrase, match_level, data)
            return None # until a match is found
        else:
            LOG.info("NO USB Device, Passing on this request")
            return None

    def CPS_start(self, phrase, data):
        """ Starts playback.
            Called by the playback control skill to start playback if the
            skill is selected (has the best match level)
        """
        LOG.info('USBMusicSkill received the following phrase and Data: ' + phrase + ' ' + data['track'])
        url = data['track']
        self.audioservice.play(url)  #
        pass

    def monitor_usb(self, my_id, terminate):
        LOG.info("USB Monitoring Loop Started!")
        while True:
            time.sleep(1) # Todo make the polling time a variable or make it a separate thread
            # get the status of the connected usb device
            self.status = usbdev.isDeviceConnected()
            if self.status != self.prev_status:
                LOG.info("Status Changed!")
                self.prev_status = self.status
                if self.status:
                    LOG.info("Device Inserted!")
                    device = usbdev.getDevData()
                    # get the path (currently set for Rpi, can be changed)
                    self.path = usbdev.getMountPathUsbDevice()
                    LOG.info("Stat: " + str(self.status))
                    LOG.info("dev: " + str(device))
                    LOG.info("path: " + str(self.path))
                    LOG.info("---------------------------------")
                    self.speak_dialog('update.library', expect_response=False)
                    self.song_list = self.create_library(self.path)
                else:
                    LOG.info("Device Removed!")
                    self.speak_dialog('usb.removed', expect_response=False)
                    self.song_list = []
                    self.path = ""
        #usbdev.stopListener(observer)

    def create_library(self, usb_path):
        new_library = []
        for root, d_names, f_names in os.walk(str(usb_path)):
            for fileName in f_names:
                if "mp3" in str(fileName):
                    song_path = str(root) + "/" + str(fileName)
                    LOG.info("Found mp3: " + song_path)
                    audio = EasyID3(song_path)
                    try:
                        if len(audio["title"]):
                            self.song_title = audio["title"][0]
                        else:
                            self.song_title = ""
                        if len(audio["artist"]):
                            self.song_artist = audio["artist"][0]
                        else:
                            self.song_artist = ""
                        if len(audio["album"]):
                            self.song_album = audio["album"][0]
                        else:
                            self.song_album = ""
                    except:
                        pass
                    info = {
                        "location": song_path,
                        "label": self.song_title,
                        "artist": self.song_artist,
                        "album": self.song_album
                    }
                    new_library.append(info)
        # Todo announce how many songs where found
        self.speak_dialog('scan.complete', expect_response=False)
        song_count = len(new_library)
        LOG.info("Added: " + str(song_count) + " to the library from the USB Device")
        return new_library

    @intent_handler(IntentBuilder('UpdateLibraryIntent').require("UpdateKeyword").require("USBKeyword").
                    require("LibraryKeyword").build())
    def handle_update_library_intent(self, message):
        LOG.info("Called Update Library Intent")
        if self.status:
            self.speak_dialog('update.library', expect_response=False)
            self.song_list = self.create_library(self.path)
        else:
            # Play Music Added here
            LOG.info("USB Device Not Detected")

    def stop(self):
        pass

def create_skill():
    return USBMusicSkill()