from mycroft.skills.common_play_skill import CommonPlaySkill, CPSMatchLevel
from adapt.intent import IntentBuilder
from mycroft.skills.core import intent_handler, intent_file_handler
from mycroft.util.log import LOG

import threading

from .usbScan import usbdev

import re
import time
import os
from os.path import dirname
from mutagen.easyid3 import EasyID3


class NewThread:
    id = 0
    idStop = False
    idThread = threading.Thread


class USBMusicSkill(CommonPlaySkill):

    def __init__(self):
        super(USBMusicSkill, self).__init__('USBMusicSkill')
        self.song_list = []
        self.prev_status = False
        self.song_artist = ""
        self.song_label = ""
        self.song_album = ""
        self.prev_status = False
        self.status = False
        self.path = ""
        self.usb_monitor = NewThread
        self.usbdevice = usbdev
        self.observer = self.usbdevice.startListener()
        LOG.info("USB Music Skill Loaded!")

    def initialize(self):
        self.load_data_files(dirname(__file__))
        LOG.info("USB Music Skill Initialized!")
        self.init_usb_monitor_thread()

    def init_usb_monitor_thread(self):  # creates the workout thread
        self.usb_monitor.idStop = False
        self.usb_monitor.id = 101
        self.usb_monitor.idThread = threading.Thread(target=self.start_usb_thread,
                                                     args=(self.usb_monitor.id,
                                                           lambda: self.usb_monitor.idStop))
        self.usb_monitor.idThread.start()

    def halt_usb_monitor_thread(self):  # requests an end to the workout
        try:
            self.usb_monitor.id = 101
            self.usb_monitor.idStop = True
            self.usb_monitor.idThread.join()
        except Exception as e:
            LOG.error(e)  # if there is an error attempting the workout then here....

    def numeric_replace(self, in_words=""):
        word_list = in_words.split()
        return_list = []
        for each_word in word_list:
            try:
                new_word = w2n.word_to_num(each_word)
            except Exception as e:
                # LOG.info(e)
                new_word = each_word
            return_list.append(new_word)
            return_string = ' '.join(str(e) for e in return_list)
        return return_string


    def CPS_match_query_phrase(self, phrase):
        """
            The method is invoked by the PlayBackControlSkill.
        """
        LOG.info('USBMusicSkill received the following phrase: ' + phrase)
        if self.status:  # Confirm the USB is inserted
            LOG.info("USBMusicSkill is Searching for requested media...")
            play_request = self.parse_music_utterance(phrase)  # get the requested Music Item
            LOG.info("USBMusicSkill Parse Routine Returned: " + str(play_request))
            music_playlist = self.search_music_library(play_request[0],
                                                       category=play_request[1])  # search for the item in the library

            if music_playlist is None:
                return None  # until a match is found
            else:
                if len(music_playlist) > 0:
                    match_level = CPSMatchLevel.EXACT
                    data = music_playlist
                    LOG.info('Music found that matched the request!')
                    return phrase, match_level, data
                else:
                    return None  # until a match is found
        else:
            LOG.info("NO USB Device, Passing on this request")
            return None

    def parse_music_utterance(self, phrase):
        # returns what was spoken in the utterance
        return_type = "any"
        str_request = str(phrase)
        LOG.info("Parse Music Received: " + str_request)
        primary_regex = r"((?<=album) (?P<album>.*$))|((?<=artist) (?P<artist>.*$))|((?<=song) (?P<label>.*$))"
        if str_request.find('some') != -1:
            secondary_regex = r"((?<=some) (?P<any>.*$))"
        else:
            secondary_regex = r"((?<=play) (?P<any>.*$))"
        key_found = re.search(primary_regex, str_request)
        if key_found:
            LOG.info("Primary Regex Key Found")
            if key_found.group("label"):
                LOG.info("found label")
                return_item = key_found.group("label")
                return_type = "label"
            elif key_found.group("artist"):
                LOG.info("found artist")
                return_item = key_found.group("artist")
                return_type = "artist"
            elif key_found.group("album"):
                LOG.info("found album")
                return_item = key_found.group("album")
                return_type = "album"
        else:
            LOG.info("Primary Regex Key Not Found")
            key_found = re.search(secondary_regex, str_request)
            if key_found.group("any"):
                LOG.info("Secondary Regex Key Found")
                return_item = key_found.group("any")
                return_type = "any"
            else:
                LOG.info("Secondary Regex Key Not Found")
                return_item = "none"
                return_type = "none"
        # Returns the item that was requested and the type of the requested item ie. artist, album, label
        return return_item, return_type

    def search_music_library(self, search_string, category="any"):
        found_list = []  # this is a dict that will contain all the items found in the library
        LOG.info("searching the music library for: " + search_string + ", " + category)
        if category == "any":
            found_list = self.search_music_item(search_string, category="label")
            if len(found_list) > 0:
                return found_list
            LOG.info("Label: " + search_string + ", Not Found!")
            found_list = self.search_music_item(search_string, category="artist")
            if len(found_list) > 0:
                return found_list
            LOG.info("Artist: " + search_string + ", Not Found!")
            found_list = self.search_music_item(search_string, category="album")
            if len(found_list) == 0:
                LOG.info("Album: " + search_string + ", Not Found!")
                return
        else:
            found_list = self.search_music_item(search_string, category=str(category))
        if len(found_list) > 0:
            return found_list

    def search_music_item(self, search_item, category="label"):
        # category options: label, artist, album
        LOG.info('Continuing to search the library')
        search_item = self.numeric_replace(search_item)
        found_list = []  # this is a dict of all the items found that match the search
        search_words = search_item.replace("-", "").lower().split()
        # check each movie in the list for strings that match all the words in the search
        for each_song in self.song_list:  # check each song in the list for the one we are looking for
            LOG.info('Comparing to song: ' + str(each_song))
            item_name = each_song[category].replace("-", "")
            if len(item_name) > 0:
                item_name = self.numeric_replace(item_name)
                if all(words in item_name.lower() for words in search_words):
                    found_length = len(each_song['label'].split())
                    info = {
                        "location": each_song['location'],
                        "label": each_song['label'],
                        "album": each_song['album'],
                        "artist": each_song['artist']
                    }
                    found_list.append(info)
        LOG.info('Found the following songs: ' + str(found_list))
        # remove duplicates
        temp_list = []  # this is a dict
        for each_song in found_list:
            song_title = str(each_song['label'])
            if song_title not in str(temp_list):
                temp_list.append(info)
            else:
                if len(each_song['label']) == len(song_title):
                    LOG.info('found duplicate')
                else:
                    temp_list.append(info)
        found_list = temp_list
        LOG.info('Filtered the following songs: ' + str(found_list))
        return found_list  # returns a dictionary of matched movies

    def CPS_start(self, phrase, data):
        """ Starts playback.
            Called by the playback control skill to start playback if the
            skill is selected (has the best match level)
        """
        LOG.info('USBMusicSkill, Playback received the following phrase and Data: ' + phrase + ' ' + str(data))
        #url = data['track']
        #self.audioservice.play(url)  #
        pass

    def start_usb_thread(self, my_id, terminate):
        LOG.info("USB Monitoring Loop Started!")
        while not terminate():  # wait while this interval completes
            time.sleep(1)  # Todo make the polling time a variable or make it a separate thread
            # get the status of the connected usb device
            self.status = self.usbdevice.isDeviceConnected()
            # LOG.info("Checking USB Device: " + str(self.status))
            if self.status != self.prev_status:
                LOG.info("USB Status Changed!")
                self.prev_status = self.status
                if self.status:  #Device inserted
                    LOG.info("Device Inserted!")
                    device = self.usbdevice.getDevData()
                    # mount the device and get the path
                    self.path = self.usbdevice.getMountPathUsbDevice('mycroft')  #todo add sudo password to websettings
                    LOG.info("Stat: " + str(self.status))
                    LOG.info("dev: " + str(device))
                    LOG.info("path: " + str(self.path))
                    LOG.info("---------------------------------")
                    self.speak_dialog('update.library', expect_response=False)
                    self.song_list = self.create_library(self.path)
                    LOG.info(str(self.song_list))
                else:
                    # unmount the path
                    self.usbdevice.uMountPathUsbDevice('mycroft')  #todo add sudo password to websettings
                    LOG.info("Device Removed!")
                    self.speak_dialog('usb.removed', expect_response=False)
                    self.song_list = []
                    self.path = ""
        self.usbdevice.stopListener(self.observer)

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
                            self.song_label = audio["title"][0]
                        else:
                            self.song_label = ""
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
                        "label": self.song_label,
                        "artist": self.song_artist,
                        "album": self.song_album
                    }
                    new_library.append(info)
        # Todo announce how many songs where found
        song_count = len(new_library)
        self.speak_dialog('scan.complete', data={"count": str(song_count)}, expect_response=False)
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
        self.halt_usb_monitor_thread()
        pass

def create_skill():
    return USBMusicSkill()