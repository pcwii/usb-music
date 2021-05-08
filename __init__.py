from mycroft.skills.common_play_skill import CommonPlaySkill, CPSMatchLevel
from adapt.intent import IntentBuilder
from mycroft.skills.core import intent_handler, intent_file_handler
from mycroft.util.log import LOG
from mycroft.skills.audioservice import AudioService
from mycroft.audio.services.vlc import VlcService
from mycroft.audio import wait_while_speaking

from websocket import create_connection

import threading
from importlib import reload
import sys
import json

from .usbScan import usbdev
## from .usbScan import *

import re
import time
import os
from os.path import dirname

import random

from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.aac import AAC
from mutagen.mp4 import MP4

for each_module in sys.modules:
    if "usbScan" in each_module:
        LOG.info("Attempting to reload usbScan Module: " + str(each_module))
        reload(sys.modules[each_module])


class NewThread:
    id = 0
    idStop = False
    idThread = threading.Thread

MUSIC_TYPES = ['mp3', 'm4a', 'flac', 'wav', 'wma','aac']

class USBMusicSkill(CommonPlaySkill):

    def __init__(self):
        super(USBMusicSkill, self).__init__('USBMusicSkill')
        self.mediaplayer = VlcService(config={'low_volume': 10, 'duck': True})
        self.song_list = []
        self.prev_status = False
        self.song_artist = ""
        self.song_label = ""
        self.song_album = ""
        self.auto_play = False
        self.insert_command = ""
        self.command_enable = False
        self.prev_status = False
        self.status = False
        self.library_ready = False
        self.path = ""
        self.local_path = ""
        self.smb_path = ""
        self.smb_uname = ""
        self.smb_pass = ""

        self.usb_monitor = NewThread
        self.usbdevice = usbdev
        self.observer = self.usbdevice.startListener()
        #self.audio_service = None
        self.audio_state = 'stopped'  # 'playing', 'stopped'
        LOG.info("USB Music Skill Loaded!")

    def initialize(self):
        self.load_data_files(dirname(__file__))
        #self.audio_service = AudioService(self.bus)
        LOG.info("USB Music Skill Initialized!")
        self.halt_usb_monitor_thread()
        self.init_usb_monitor_thread()
        self.settings_change_callback = self.on_websettings_changed
        self.on_websettings_changed()

    def on_websettings_changed(self):  # called when updating mycroft home page
        self.auto_play = self.settings.get("auto_play", False)  # used to enable / disable auto_play
        self.local_path = self.settings.get("local_path", "/home/pi/Music")
        self.smb_path = self.settings.get("smb_path", "//192.168.0.20/SMBMusic")
        self.smb_uname = self.settings.get("smb_uname", "guest")
        self.smb_pass = self.settings.get("smb_pass", "")
        self.insert_command = self.settings.get("insert_command", "")
        if len(self.insert_command) > 0:
            self.command_enable = self.settings.get("command_enable", False)
        else:
            LOG.info('No Command Specified, Enable Set to: False')
            self.command_enable = False
        LOG.info('USB-Music Settings Changed, Command Enable now: ' + str(self.command_enable))
        LOG.info('USB-Music Settings Changed, AutoPlay now: ' + str(self.auto_play))
        LOG.info('USB-Music Settings Changed, SMB Path now: ' + str(self.smb_path))
        LOG.info('USB-Music Settings Changed, Local Path now: ' + str(self.local_path))

    def send_message(self, message):  # Sends the remote received commands to the messagebus
        LOG.info("Sending a command to the message bus: " + message)
        payload = json.dumps({
            "type": "recognizer_loop:utterance",
            "context": "",
            "data": {
                "utterances": [message]
            }
        })
        uri = 'ws://localhost:8181/core'
        ws = create_connection(uri)
        ws.send(payload)
        ws.close()

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

    def parse_music_utterance(self, phrase):
        # Todo: move Regex to file for language support
        # Todo: This needs to be refactored as it is not a sustainable way to search music
        # returns what was spoken in the utterance
        return_item = "none"
        return_type = "any"
        str_request = str(phrase)
        LOG.info("Parse Music Received: " + str_request)
        primary_regex = r"((?<=album) (?P<album>.*$))|((?<=by) (?P<artist1>.*$))|((?<=artist) (?P<artist>.*$))|((?<=song) (?P<label>.*$))"
        secondary_regex = None
        if str_request.find('some') != -1:
            secondary_regex = r"((?<=some) (?P<any>.*$))"
        elif str_request.find('my') != -1:
            secondary_regex = r"((?<=my) (?P<any>.*$))"
        elif str_request.find('all') != -1:
            secondary_regex = r"((?<=all) (?P<any>.*$))"
        elif str_request.find('any') != -1:
            secondary_regex = r"((?<=any) (?P<any>.*$))"
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
            elif key_found.group("artist1"):
                LOG.info("found artist")
                return_item = key_found.group("artist")
                return_type = "artist"
            elif key_found.group("album"):
                LOG.info("found album")
                return_item = key_found.group("album")
                return_type = "album"
        else:
            LOG.info("Primary Regex Key Not Found")
            if secondary_regex:
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
            if len(found_list) > 0:
                return found_list
            found_list = self.search_music_item(search_string, category="location")
            if len(found_list) > 0:
                return found_list
            if len(found_list) == 0:
                LOG.info("Album: " + search_string + ", Not Found!")
                return
        else:
            found_list = self.search_music_item(search_string, category=str(category))
        if len(found_list) > 0:
            return found_list

    def search_music_item(self, search_item, category="label"):
        # category options: label, artist, album
        search_item = self.numeric_replace(search_item)
        found_list = []  # this is a dict of all the items found that match the search
        search_words = search_item.replace("-", "").lower().split()
        # check each song in the list for strings that match all the words in the search
        for each_song in self.song_list:  # check each song in the list for the one we are looking for
            item_name = each_song[category].replace("-", "")
            if len(item_name) > 0:
                item_name = self.numeric_replace(item_name)
                if all(words in item_name.lower() for words in search_words):
                    found_length = len(each_song['label'].split())
                    info = {
                        "location": each_song['location'],
                        "label": each_song['label'],
                        "album": each_song['album'],
                        "artist": each_song['artist'],
                        "source": each_song['source']
                    }
                    found_list.append(info)
        LOG.info('Found the following songs: ' + str(found_list))
        # remove duplicates
        temp_list = []  # this is a dict
        for each_song in found_list:
            info = {
                "location": each_song['location'],
                "label": each_song['label'],
                "album": each_song['album'],
                "artist": each_song['artist'],
                "source": each_song['source']
            }  # Todo this is missing in the kodi skill????
            song_title = str(each_song['label'])
            if song_title not in str(temp_list):
                temp_list.append(info)
            else:
                if len(each_song['label']) == len(song_title):
                    LOG.info('found duplicate')
                else:
                    temp_list.append(info)
        found_list = temp_list
        return found_list  # returns a dictionary of matched movies

    def merge_library(self, dict1, dict2):
        return dict1 + dict2

    def start_usb_thread(self, my_id, terminate):
        """
        This thread monitors the USB port for an insertion / removal event
        """
        # Todo automatically play when stick is inserted
        LOG.info("USB Monitoring Loop Started!")
        while not terminate():  # wait while this interval completes
            time.sleep(1)  # Todo make the polling time a variable or make it a separate thread
            # get the status of the connected usb device
            self.status = self.usbdevice.isDeviceConnected()
            if self.status != self.prev_status:
                LOG.info("USB Status Changed!")
                self.prev_status = self.status
                if self.status:  # Device inserted
                    # remove any existing mount points
                    self.usbdevice.uMountPathUsbDevice()
                    LOG.info("Device Inserted!")
                    device = self.usbdevice.getDevData()
                    # mount the device and get the path
                    self.path = self.usbdevice.getMountPathUsbDevice()
                    LOG.info("Stat: " + str(self.status))
                    LOG.info("dev: " + str(device))
                    LOG.info("path: " + str(self.path))
                    LOG.info("---------------------------------")
                    self.speak_dialog('update.library', data={"source": str("usb")}, expect_response=False)
                    wait_while_speaking()
                    self.song_list = [i for i in self.song_list if not (i['source'] == 'usb')]
                    self.song_list = self.merge_library(self.song_list, self.create_library(self.path, "usb"))
                    if self.command_enable:
                        self.send_message(self.insert_command)
                    if self.auto_play:
                        self.play_all(self.song_list)
                else:
                    #self.audio_service.stop()
                    self.mediaplayer.stop()
                    # unmount the path
                    self.usbdevice.uMountPathUsbDevice()
                    LOG.info("Device Removed!")
                    # Todo remove context "USB" so all play requests start with this skill
                    self.speak_dialog('usb.removed', expect_response=False)
                    wait_while_speaking()
                    self.song_list = []
                    self.path = ""
                    self.on_websettings_changed()
        self.usbdevice.stopListener(self.observer)

    def play_all(self, library):
        LOG.info('Automatically playing the USB Device')
        tracklist = []
        for each_song in library:
            LOG.info("CPS Now Playing... " + each_song['label'] + " from location: " + each_song['location'])
            url = each_song['location']
            tracklist.append(url)
        random.shuffle(tracklist)
        self.speak_dialog('now.playing')
        wait_while_speaking()
        self.mediaplayer.add_list(tracklist)
        self.mediaplayer.play()
        #self.audio_service.play(tracklist)

        self.audio_state = 'playing'

    def create_library(self, source_path, source_type="usb"):
        # Todo - add regex to remove numbers from the begining of filenames to get song name (\d{1,3}|)( - |)(?P<song_Name>.+)
        self.library_ready = False
        new_library = []
        for root, d_names, f_names in os.walk(str(source_path)):
            for fileName in f_names:
                foundType = [musicType for musicType in MUSIC_TYPES if (musicType.lower() in fileName.lower())]
                if bool(foundType):
                    song_path = str(root) + "/" + str(fileName)
                    try:
                        if "flac" in str(foundType[0].lower):  # add flac filter
                            audio = FLAC(song_path)
                            # LOG.info("Checking FLAC Tags" + str(audio))
                        elif "aac" in str(foundType[0].lower):  # add flac filter:
                            audio = AAC(song_path)
                            #LOG.info("Checking ID3 Tags" + str(audio))
                        elif "mp3" in str(foundType[0].lower):  # add flac filter:
                            audio = EasyID3(song_path)
                            #LOG.info("Checking ID3 Tags" + str(audio))
                        elif "m4a" in str(foundType[0].lower):  # add flac filter:
                            audio = MP4(song_path)
                            #LOG.info("Checking ID3 Tags" + str(audio))
                        if len(audio) > 0:  # An ID3 tag found
                            if audio['title'] is None:
                                trim_length = (len(str(foundType[0])) + 1) * -1
                                self.song_label = str(fileName)[:trim_length]
                            else:
                                self.song_label = audio['title'][0]
                                LOG.info("Checking FLAC title: " + self.song_label)
                            if audio['artist'] is None:
                                if audio['Contributing artists']:
                                    self.song_artist = audio['Contributing artists'][0]
                                else:
                                    self.song_artist = ""
                            else:
                                self.song_artist = audio['artist'][0]
                            if audio['album'] is None:
                                self.song_album = ""
                            else:
                                self.song_album = audio['album'][0]
                        else:  # There was no ID3 Tag found, use filename as song title
                            trim_length = (len(str(foundType[0])) + 1) * -1
                            self.song_label = str(fileName)[:trim_length]
                            self.song_artist = ""
                            self.song_album = ""
                    except:
                        trim_length = (len(str(foundType[0])) + 1) * -1
                        self.song_label = str(fileName)[:trim_length]
                        self.song_artist = ""
                        self.song_album = ""
                        pass
                    info = {
                        "location": song_path,
                        "label": self.song_label,
                        "artist": self.song_artist,
                        "album": self.song_album,
                        "source": str(source_type)
                    }
                    new_library.append(info)
        song_count = len(new_library)
        if song_count == 0:
            self.speak_dialog('no.files', data={"source": str(source_type)}, expect_response=False)
        else:
            self.speak_dialog('scan.complete', data={"count": str(song_count), "source": str(source_type)},
                              expect_response=False)
        wait_while_speaking()
        LOG.info("Added: " + str(song_count) + " to the library from the " + str(source_type) + " Device")
        self.library_ready = True
        return new_library

    def CPS_match_query_phrase(self, phrase):
        """
            The method is invoked by the PlayBackControlSkill.
        """
        LOG.info('USBMusicSkill received the following phrase: ' + phrase)
        if self.status or self.library_ready:  # Confirm the USB is inserted
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
            LOG.info("Device or Library Not Ready, Passing on this request")
            return None

    def CPS_start(self, phrase, data):
        """ Starts playback.
            Called by the playback control skill to start playback if the
            skill is selected (has the best match level)
        """
        tracklist = []
        LOG.info('USBMusicSkill, Playback received the following phrase and Data: ' + phrase + ' ' + str(data))
        for each_song in data:
            LOG.info("CPS Now Playing... " + each_song['label'] + " from location: " + each_song['location'])
            url = each_song['location']
            tracklist.append(url)
        #LOG.info(str(tracklist))
        self.speak_dialog('now.playing')
        wait_while_speaking()
        #self.audio_service.play(tracklist)
        #random.shuffle(tracklist)
        self.mediaplayer.add_list(tracklist)
        self.mediaplayer.play()
        self.audio_state = 'playing'
        pass

    @intent_handler(IntentBuilder('').require("UpdateKeyword").require("USBKeyword").require("LibraryKeyword"))
    def handle_update_usb_library_intent(self, message):
        LOG.info("Called Update Library Intent")
        if self.usbdevice.isDeviceConnected():
            device = self.usbdevice.getDevData()
            # mount the device and get the path
            self.path = self.usbdevice.getMountPathUsbDevice()
            self.speak_dialog('update.library', data={"source": str(message.data.get("USBKeyword"))},
                              expect_response=False)
            wait_while_speaking()
            self.song_list = [i for i in self.song_list if not (i['source'] == 'usb')]
            self.song_list = self.merge_library(self.song_list, self.create_library(self.path, "usb"))
        else:
            self.usbdevice.uMountPathUsbDevice()
            # Play Music Added here
            self.speak_dialog('usb.not.mounted', expect_response=False)
            wait_while_speaking()
            LOG.info("USB Device Not Detected")
    # Todo: Add an unmount / release command

    @intent_handler(IntentBuilder('').require("RemoveKeyword").require("USBKeyword"))
    def handle_remove_usb_intent(self, message):
        self.usbdevice.uMountPathUsbDevice()
        LOG.info("Device Removed!")

    @intent_handler(IntentBuilder('').require("UpdateKeyword").require("NetworkKeyword").require("LibraryKeyword"))
    def handle_get_smb_music_intent(self, message):
        self.path = self.usbdevice.MountSMBPath(self.smb_path, self.smb_uname, self.smb_pass)
        self.speak_dialog('update.library', data={"source": str(message.data.get("NetworkKeyword"))},
                          expect_response=False)
        wait_while_speaking()
        self.song_list = [i for i in self.song_list if not (i['source'] == 'smb')]
        self.song_list = self.merge_library(self.song_list, self.create_library(self.path, "smb"))
        LOG.info("SMB Mounted!")

    @intent_handler(IntentBuilder('').require("UpdateKeyword").require("LocalKeyword").require("LibraryKeyword"))
    def handle_get_local_music_intent(self, message):
        self.path = self.local_path
        self.speak_dialog('update.library', data={"source": str(message.data.get("LocalKeyword"))},
                          expect_response=False)
        wait_while_speaking()
        self.song_list = [i for i in self.song_list if not (i['source'] == 'local')]
        self.song_list = self.merge_library(self.song_list, self.create_library(self.path, "local"))
        LOG.info("Local Mounted!")

    @intent_handler(IntentBuilder('').require("UpdateKeyword").require("MusicKeyword").require("LibraryKeyword"))
    def handle_get_All_available_intent(self, message):
        self.path = self.usbdevice.MountSMBPath(self.smb_path, self.smb_uname, self.smb_pass)
        self.speak_dialog('update.library', data={"source": str(message.data.get("MusicKeyword"))},
                          expect_response=False)
        wait_while_speaking()
        self.song_list = [i for i in self.song_list if not (i['source'] == 'smb')]
        self.song_list = self.merge_library(self.song_list, self.create_library(self.path, "smb"))
        LOG.info("SMB Mounted!")
        self.path = self.local_path
        self.song_list = [i for i in self.song_list if not (i['source'] == 'local')]
        self.song_list = self.merge_library(self.song_list, self.create_library(self.path, "local"))
        LOG.info("Local Mounted!")
        if self.usbdevice.isDeviceConnected():
            device = self.usbdevice.getDevData()
            # mount the device and get the path
            self.path = self.usbdevice.getMountPathUsbDevice()
            self.speak_dialog('update.library', data={"source": str(message.data.get("USBKeyword"))},
                              expect_response=False)
            wait_while_speaking()
            self.song_list = [i for i in self.song_list if not (i['source'] == 'usb')]
            self.song_list = self.merge_library(self.song_list, self.create_library(self.path, "usb"))

    @intent_handler(IntentBuilder('').require("StartKeyword").require("USBKeyword").require('ScanKeyword'))
    def handle_start_usb_intent(self, message):
        LOG.info('Thread Running: ' + str(self.usb_monitor.idThread.isAlive()))
        if self.usb_monitor.idThread.isAlive():
            LOG.info("Scan is already running!")
        else:
            LOG.info("Scan should start!")
            self.init_usb_monitor_thread()

    @intent_handler(IntentBuilder('').require("ShowKeyword").require("MusicKeyword").require('LibraryKeyword'))
    def handle_show_music_library_intent(self, message):
        LOG.info(str(self.song_list))
        LOG.info('Library Size: ' + str(len(self.song_list)))

    def stop(self):
        if self.audio_state == 'playing':
            #self.audio_service.stop()
            self.mediaplayer.stop()

            LOG.debug('Stopping stream')
        self.audio_state = 'stopped'
        return True

        #LOG.info('Stopping USB Monitor Thread!')
        #self.halt_usb_monitor_thread()
        pass


def create_skill():
    return USBMusicSkill()