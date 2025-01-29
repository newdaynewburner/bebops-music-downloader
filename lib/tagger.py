"""
lib/tagger.py

Handle retrieval of tag data and appending it to downloaded
MP3 files
"""

import os
import eyed3
from pytubefix import YouTube, Playlist

class TagManager(object):
	""" Fetches tag data according to tag mode specified
	at runtime and appends them to the appropriate MP3 file
	
	Methods:
		__init__() - Initialize the object
		fetch_song_tags() - Fetch song tag data
		fetch_album_tags() - Fetch album tag data
		append_tags() - Add song metadata to file
	"""
	
	def __init__(self, debug, quiet, tag_mode):
		""" Initialize the object
		
		Arguments:
			self - object - This object
			debug - bool - Debugging mode
			quiet - bool - Suppress output
			tag_mode - string - Specified tag mode
			
		Returns:
			None
		"""
		
		self.debug = debug
		self.quiet = quiet
		self.tag_mode = tag_mode
		
	def fetch_song_tags(self, yt, video_num=None, album_tags=None):
		""" Retrieve tag data for individual songs
		
		Arguments:
			self - object - This object
			yt - YouTube object - PyTube YouTube object for the song's YT URL
			video_num - int - Position of video in playlist
			album_tags - dict - Album tag data
			
		Returns:
			tags - dict - Song tag data
		"""
		
		tags = {}
		if self.tag_mode == "manual":
			# Manual tag mode
			if self.quiet is not True:
				print("[*] Please provide tag data below. Leave blank to use remote value")
				
			tags["title"] = input("[i] Title ({}): ".format(yt.title))
			if album_tags is not None:
				tags["artist"] = album_tags["artist"]
			else:
				tags["artist"] = input("[i] Artist ({}): ".format(yt.author))
			if album_tags is not None:
				tags["album"] = album_tags["title"]
				tags["track_num"] = video_num
				tags["release_year"] = album_tags["release_year"]
			else:
				tags["album"] = None
				tags["track_num"] = None
				tags["release_year"] = None
			if album_tags is not None:
				tags["genre"] = album_tags["genre"]
			else:
				tags["genre"] = input("[i] Genre: ")
			
			if tags["title"] == "":
				tags["title"] = yt.title
			if tags["artist"] == "":
				tags["artist"] = yt.author
			if tags["genre"] == "":
				tags["genre"] = None
				
		elif self.tag_mode == "auto":
			# Auto tag mode
			if self.quiet is not True:
				print("[*] Fetching tag data...")
				
			tags["title"] = yt.title
			if album_tags is not None:
				tags["artist"] = album_tags["artist"]
				tags["album"] = album_tags["title"]
				tags["track_num"] = video_num
				tags["release_year"] = album_tags
				tags["genre"] = album_tags["genre"]
			else:
				tags["artist"] = yt.author
				tags["album"] = None
				tags["track_num"] = None
				tags["release_year"] = None
				tags["genre"] = None
		
		else:
			# None tag mode
			tags = None
			
		return tags
		
	def fetch_album_tags(self, pl):
		""" Fetch album tag data
		
		Arguments:
			self - object - This object
			pl - Playlist object - Current Playlist object instance
			
		Returns:
			album_tags - dict - Album tag data
		"""
		
		album_tags = {}
		if self.tag_mode == "manual":
			# Manual tag mode
			if self.quiet is not True:
				print("[*] Please provide album tag data below. Leave blank to use remote value")
				
			album_tags["title"] = input("[i] Album title ({}): ".format(pl.title))
			album_tags["artist"] = input("[i] Artist ({}): ".format(pl.owner))
			album_tags["release_year"] = input("[i] Release year: ({}): ".format(pl.last_updated))
			album_tags["genre"] = input("[i] Genre: ")
			
			if album_tags["title"] == "":
				album_tags["title"] = pl.title
			if album_tags["artist"] == "":
				album_tags["artist"] = pl.owner
			if album_tags["release_year"] == "":
				album_tags["release_year"] = pl.last_updated
			if album_tags["genre"] == "":
				album_tags["genre"] = None
				
		elif self.tag_mode == "auto":
			# Auto tag mode
			if self.quiet is not True:
				print("[*] Fetching album tag data...")
				
			album_tags["title"] = pl.title
			album_tags["artist"] = pl.owner
			album_tags["release_year"] = pl.last_updated
			album_tags["genre"] = None
		
		else:
			# None tag mode
			album_tags = None
			
		return album_tags
		
	def append_tags(self, mp3_filepath, tags):
		""" Add song metadata to file
		
		Arguments:
			self - object - This object
			mp3_file - filepath - Full path to file to add tags to
			tags - dict - Tag data to add to file
			
		Returns:
			tags_added - list - List of what tags were added to the file
		"""
		
		tags_added = []
		if tags is not None:
			mp3_file = eyed3.load(mp3_filepath)
			mp3_file.initTag()
			
			if tags["title"] is not None:
				mp3_file.tag.title = tags["title"]
				tags_added.append("title")
			if tags["artist"] is not None:
				mp3_file.tag.artist = tags["artist"]
				tags_added.append("artist")
			if tags["album"] is not None:
				mp3_file.tag.album = tags["album"]
				tags_added.append("album")
			if tags["track_num"] is not None:
				mp3_file.tag.track_num = tags["track_num"]
				tags_added.append("track_num")
			if tags["release_year"] is not None:
				mp3_file.tag.year = int(tags["release_year"])
				tags_added.append("release_year")
			if tags["genre"] is not None:
				mp3_file.tag.genre = tags["genre"]
				tags_added.append("genre")
			mp3_file.tag.save()
		
		return tags_added
