#!/usr/bin/python3

"""
Bebop's Music Downloader

A tool for downloading music from YouTube in MP3 format. It can 
download either individual songs (from videos) or entire albums 
(from playlists), and supports the adding of tags to the downloaded 
MP3 files. Tag data can be retrieved and entered automatically,
manually, or not at all. Oriented to people who want to build well 
organized and nicely tagged music collections. 
"""

import os
import sys
import getopt
import configparser
#from pytube import YouTube, Playlist # Obsolete/not working. Replaced by pytubefix
from pytubefix import YouTube, Playlist

from lib import tagger
from lib import downloader

def main(config, settings, dl_targets):
	""" Initiate and control the download and other
	related processes
	
	Arguments:
		config - ConfigParser() object - Readable configuration file object
		settings - tuple - Contains the script settings to be used
		dl_targets - tuple - Contains the YT video or playlist URL to download from
		
	Returns:
		None
	"""
	
	# Unpack settings
	debug = settings[0]
	quiet = settings[1]
	outdir = settings[2]
	multithreading = settings[3]
	tag_mode = settings[4]
	
	# Display banner
	if config["Display"]["show_banner"] == True:
		if quiet is not True:
			print("############################")
			print("# Bebop's Music Downloader #")
			print("############################")
			print("")
			print("+---------------+")
			print("")
	
	#########################
	# HANDLE SONG DOWNLOADS #
	#########################
	if dl_targets[0] is not None:
		video_url = dl_targets[0]
		yt = YouTube(video_url, "WEB")
		
		if quiet is not True:
			print("[*] Initializing song download...")
			if debug is True:
				print("\t[DEBUG] Video URL: {}".format(video_url))
				print("\t[DEBUG] Download location: {}".format(outdir))
				print("\t[DEBUG] Tag mode: {}".format(tag_mode))
			if multithreading is True:
				print("[NOTE] Multithreaded downloading has been enabled, but")
				print("[NOTE] is unnecessary for downloading single songs")
			print("\t[**] Video title: {}".format(yt.title))
			
		# Get song tag data
		tag_manager = tagger.TagManager(debug, quiet, tag_mode)
		# DEBUGGING
		if debug is True:
			print("[DEBUG] Created new TagManager object with values: {0}, {1}, {2}".format(debug, quiet, tag_mode))
		tags = tag_manager.fetch_song_tags(yt)
		
		# Build download queue
		download_manager = downloader.DownloadManager(debug, quiet, multithreading, tag_manager)
		
		if tag_mode == "none":
			mp3_file = "{0} - {1}.mp3".format(yt.author, yt.title)
		else:
			mp3_file = "{0} - {1}.mp3".format(tags["artist"], tags["title"])
		dl_location = os.path.join(outdir, mp3_file)
		
		if quiet is not True:
			print("\t[**] Song filename: {}".format(mp3_file))
		
		download_manager.add_to_queue(video_url, dl_location, tags)
		
		# Download song
		download_manager.download()
			
	##########################
	# HANDLE ALBUM DOWNLOADS #
	##########################
	if dl_targets[1] is not None:
		playlist_url = dl_targets[1]
		pl = Playlist(playlist_url)
		
		if quiet is not True:
			print("[*] Initializing album download...")
			if debug is True:
				print("\t[DEBUG] Playlist URL: {}".format(playlist_url))
				print("\t[DEBUG] Download location: {}".format(outdir))
				print("\t[DEBUG] Tag mode: {}".format(tag_mode))
			if multithreading is True:
				print("[NOTE] Multithreaded downloading has been enabled")
			print("\t[**] Playlist title: {}".format(pl.title))
			print("\t[**] Video count: {}".format(pl.videos))
			
		# Get album tag data
		tag_manager = tagger.TagManager(debug, quiet, tag_mode)
		# DEBUGGING
		if debug is True:
			print("[DEBUG] Created new TagManager object with values: {0}, {1}, {2}".format(debug, quiet, tag_mode))
		album_tags = tag_manager.fetch_album_tags(pl)
		
		# Create album directory
		if tag_mode == "none":
			album_dir = "{0} - {1}".format(pl.owner, pl.title)
		else:
			album_dir = "{0} - {1}".format(album_tags["artist"], album_tags["title"])
		outdir = os.path.join(outdir, album_dir)
		os.mkdir(outdir)
		
		# Build download queue and fetch song tag data
		download_manager = downloader.DownloadManager(debug, quiet, multithreading, tag_manager)
		c = 0
		for video_url in pl.video_urls:
			c += 1
			yt = YouTube(video_url, "WEB")
			# Fetch song tags
			tags = tag_manager.fetch_song_tags(yt, video_num=c, album_tags=album_tags)
			
			# Generate filename and path
			mp3_file = "{0}. {1}.mp3".format(tags["track_num"], tags["title"])
			dl_location = os.path.join(outdir, mp3_file)
			
			# Add to queue
			download_manager.add_to_queue(video_url, dl_location, tags)
			
		# DEBUGGING
		if debug == True:
			download_manager.view_queue()
			
		# Start the download
		download_manager.download()
		
	return None

# Begin execution
if __name__ == "__main__":
	# Setup on first run
	copied_config_to_home = False
	if not os.path.exists(os.path.expanduser("~/.config/music-downloader")):
		os.mkdir(os.path.expanduser("~/.config/music-downloader"))
		os.system("cp config.ini ~/.config/music-downloader/config.ini")
		copied_config_to_home = True
	
	# Process CLI arguments
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hdqc:o:mt:S:A:", ("help", "debug", "quiet", "config=", "outdir=", "multithreading", "tag-mode=", "song-dl=", "album-dl="))
	except getopt.GetoptError as err_msg:
		raise Exception(err_msg)
		
	# Defaults
	debug = False
	quiet = False
	config_file = os.path.expanduser("~/.config/music-downloader/config.ini")
d	outdir = None # From config
	multithreading = None # From config
	tag_mode = None # From config
	video_url = None
	playlist_url = None
		
	for opt, arg in opts:
		if opt in ("-h", "--help"):
			# Display the help message and exit
			print("USAGE:")
			print("\t{} [-h] [-d] [-q] [-c CONFIG_FILE] [-o OUTDIR] [-m] [-t TAG_MODE] [-S VIDEO_URL] [-A PLAYLIST_URL]".format(sys.argv[0]))
			print("")
			print("Download songs and albums from YouTube in MP3 format")
			print("")
			print("OPTIONAL ARGUMENTS:")
			print("\t-h, --help\tDisplay the help message")
			print("\t-d, --debug\tEnable debugging mode")
			print("\t-q, --quiet\tSuppresses program output")
			print("\t-c, --config CONFIG_FILE\tSpecify an alternate config file")
			print("\t-o, --outdir OUTDIR\tSpecify the download location")
			print("\t-m, --multithreading\tEnable multithreaded downloads. Cam be resource intensive")
			print("\t-t, --tag-mode TAG_MODE\tControls how tags are added. Can be 'none', 'auto', or 'manual'")
			print("")
			print("REQUIRED ARGUMENTS:")
			print("\t-S, --song-dl VIDEO_URL\tDownload an individual song from given YT video")
			print("\t-A, --album-dl PLAYLIST_URL\tDownload a whole album from given YT playlist")
			exit(0)
			
		elif opt in ("-d", "--debug"):
			# Enable debug mode
			debug = True
			
		elif opt in ("-q", "--quiet"):
			# Suppress output
			quiet = True
			
		elif opt in ("-c", "--config"):
			# Specify config file to use
			config_file = arg
			
		elif opt in ("-o", "--outdir"):
			# Specify download location
			outdir = arg
			
		elif opt in ("-m", "--multithreading"):
			# Enable multithreading
			multithreading = True
			
		elif opt in ("-t", "--tag-mode"):
			# Choose how downloaded music is tagged
			if arg.lower() in ("none", "auto", "manual"):
				tag_mode = arg.lower()
			else:
				raise Exception("Invalid tag mode! Must be 'none', 'auto', or 'manual'")
				
		elif opt in ("-S", "--song-dl"):
			# Song download
			video_url = arg
			
		elif opt in ("-A", "--album-dl"):
			# Album download
			playlist_url = arg
			
	# Make sure a download target was given
	if video_url == None and playlist_url == None:
		raise Exception("Aborting! No download target given! See --help for more")
		
	# Read the configuration file and set defaults
	config = configparser.ConfigParser()
	config.read(config_file)
	# DEBUGGING
	if debug == True:
		if copied_config_to_home == True:
			print("[DEBUG] Copied config.ini file from repo to ~/.config/music-downloader/")
		print("[DEBUG] Loaded config file contents:")
		with open(config_file, "r") as f:
			for line in f.readlines():
				print("\t{}".format(line))
	
	if outdir == None:
		outdir = os.path.expanduser(config["DEFAULT"]["outdir"])
	if multithreading == None:
		multithreading = config["DEFAULT"]["multithreading"]
		if multithreading == "yes":
u			multithreading = True
		else:
			multithreading = False
	if tag_mode == None:
		tag_mode = config["DEFAULT"]["tag_mode"]
		
	# Begin downloads
	settings = (debug, quiet, outdir, multithreading, tag_mode)
	dl_targets = (video_url, playlist_url)
	main(config, settings, dl_targets)
	
	exit(0)
			
			
