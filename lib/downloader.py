"""
lib/downloader.py

Handle downloading raw audio stream and converting it
to MP3 format with FFMPEG
"""

import os
import subprocess
import threading
from pytubefix import YouTube, Playlist

def _dlthread(debug, quiet, thread_num, tag_manager, queue_item):
	""" Download thread for individual items in the download queue.
	Handles downloading of raw audio from YouTube, converting it to
	MP3 format with FFMPEG, and adding ID3 metadata tags to the
	resulting file.
	
	Arguments:
		debug - bool - Debugging mode
		quiet - bool - Suppress output
		thread_num - int - Thread number
		tag_manager - TagManager object - Instance of TagManager object
		queue_item - dict - Queue item assigned to the thread for download
		
	Returns:
		None
	"""
	
	# Unpack data from queue_item
	video_url = queue_item["video_url"]
	dl_location = queue_item["dl_location"]
	tags = queue_item["tags"]
	
	if quiet is not True:
		print("[THREAD #{}] Thread started successfully. Downloading raw audio...".format(thread_num))
	
	# Download raw audio stream
	yt = YouTube(video_url, "WEB")
	audio_stream = yt.streams.filter(only_audio=True).first()
	raw_audio_file = audio_stream.download()
	if quiet is not True:
		print("[THREAD #{}] Download complete! Beginning conversion...".format(thread_num))
	
	# Convert to MP3
	convert_command = """ffmpeg -hide_banner -loglevel error -i "{0}" "{1}" """.format(raw_audio_file, dl_location)
	subprocess.check_output(convert_command, shell=True)
	os.remove(raw_audio_file)
	if quiet is not True:
		print("[THREAD #{}] Conversion complete! Appending metadata tags to file...".format(thread_num))
		
	# Add tags to file
	tags_added = tag_manager.append_tags(dl_location, tags)
	if quiet is not True:
		print("[THREAD #{}] Tags appended to file! Song download is complete!".format(thread_num))
		if debug == True:
			print("[THREAD #{0} DEBUG] List of added tags: {1}".format(thread_num, tags_added))

class DownloadManager(object):
	""" Handle downloading raw audio stream from YouTube
	
	Methods:
		__init__() - Initialize the object
		add_to_queue() - Add a song to the download queue
		view_queue() - View details about the queue and its contents
		download() - Start downloading queue items according to download mode
	"""
	
	def __init__(self, debug, quiet, multithreading, tag_manager):
		""" Initialize the object
		
		Arguments:
			self - object - This object
			debug - bool - Debugging mode
			multithreading - bool - Multithreaded download mode
			tag_manager - TagManager object - Current instance of TagManager object
			quiet - bool - Suppress output
			
		Returns:
			None
		"""
		
		self.debug = debug
		self.quiet = quiet
		self.multithreading = multithreading
		self.tag_manager = tag_manager
		self.dl_queue = []
		self.dl_threads = []
		
	def add_to_queue(self, video_url, dl_location, tags):
		""" Add a song to the download queue
		
		Arguments:
			self - object - This object
			video_url - string - YouTube URL of the song
			dl_location - filepath - Full path with filename to download to
			tags - dict - Song tag data
			
		Returns:
			queue_length - int - New length of queue
		"""
		
		queue_item = {
			"video_url": video_url,
			"dl_location": dl_location,
			"tags": tags
		}
		self.dl_queue.append(queue_item)
		
		# DEBUGGING
		if self.debug == True:
			print("[DEBUG] Added song to queue with data:")
			print("\t[DEBUG] video_url: {}".format(video_url))
			print("\t[DEBUG] dl_location: {}".format(dl_location))
			print("\t[DEBUG] tags: {}".format(tags))
			print("[DEBUG] Current queue length: {}".format(len(self.dl_queue)))
			
		queue_length = len(self.dl_queue)
		return queue_length
		
	def view_queue(self):
		""" View details about the queue and its contents
		
		Arguments:
			self - object - This object
			
		Returns:
			None
		"""
		
		if self.quiet is not True:
			print("[*] Download queue info:")
			print("\t[**] Length: {}".format(len(self.dl_queue)))
			print("\t[**] Queue contents:")
			i = 0
			for queue_item in self.dl_queue:
				i += 1
				video_url = queue_item["video_url"]
				dl_location = queue_item["dl_location"]
				print("\t\tItem #{}".format(i))
				print("\t\tVideo URL: {}".format(video_url))
				print("\t\tDownload Location: {}".format(dl_location))
				if queue_item["tags"] is not None:
					print("\t\tHas tags: yes")
				else:
					print("\t\tHas tags: no")
				print("")
				
		return None
		
	def download(self):
		""" Start downloading queue items according to download mode
		
		Arguments:
			self - object - This object
			
		Returns:
			None
		"""
		
		# Download in multithreaded mode
		if self.multithreading == True:
			if self.quiet is not True:
				print("[*] Commencing download of all queued items in multithreaded mode...")
				print("\t[**] Building threads...")
			
			thread_num = 0
			for queue_item in self.dl_queue:
				thread_num += 1	
				new_dl_thread = threading.Thread(target=_dlthread, args=(self.debug, self.quiet, thread_num, self.tag_manager, queue_item))
				self.dl_threads.append(new_dl_thread)
				
			if self.quiet is not True:
				print("\t     ...Done!")
				print("\t[**] Starting threads...")
			
			c = 0	
			for dl_thread in self.dl_threads:
				c += 1
				dl_thread.start()
				if self.debug == True:
					print("\t[DEBUG] Started download thread #{}".format(c))
					
			if self.quiet is not True:
				print("\t     ...Done!")
				print("\t[**] Waiting for threads to finish...")
				
			for dl_thread in self.dl_threads:
				dl_thread.join()
				
			if self.quiet is not True:
				print("\t     ...Done!")
				print("\t[**] All threads finished!")
				print("[*] Download of {} items complete!".format(len(self.dl_queue)))
				
			return None
