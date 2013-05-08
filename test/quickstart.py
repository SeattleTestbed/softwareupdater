#! /usr/bin/env python

"""
quickstart.py

Written by Geremy Condra
Licensed under GPLv3
Released 12 May 2010

This program acts as a handy quickstart for TUF, helping project and repository
maintainers get into the game as quickly and painlessly as possible.

NOTES
=====
Many things in this are hardcoded in bad, bad ways. Keysizes in particular are
too small, although in the end that will all change.

In the future we will use this to provide an easy way to update metadata as well

TODO
====
much!

* scrub the console logs of sensitive information after this!
* create special error classes to handle the different errors
"""

from tuf.repo import signerlib
from tuf.repo import signercli
from tuf.repo import keystore
import tuf.util
from tuf.log import set_log_level

from os import mkdir, walk
import os.path
from os.path import sep as pathsep

from ConfigParser import ConfigParser
from shutil import copytree, move, rmtree
import tempfile

import string
import datetime


logger = tuf.log.get_logger()

# state flags
STARTED = 0
BUILD_ROOT = 1
BUILD_TARGETS = 2
BUILD_RELEASE = 3
BUILD_TIMESTAMP = 4
FINISH = 5

# test flag
TEST = False

def prompt(message, result_type=str):
	return result_type(raw_input(message))

def check_keystore_location(loc):
	"""Checks to make sure that the location given is valid, that there
	isn't already a file there, and that the user has permission to write
	there."""
	loc = os.path.abspath(loc)
	# check if the name is good
	valid_chars = string.letters + string.digits + "/._"
	for char in loc:
		if char not in valid_chars:
			raise Exception("Invalid characters in location")
	# check if there's already a file there
	if os.path.exists(loc):
		raise Exception("File already exists at the specified location")
	# make sure you have write permissions there
	if not os.access(os.path.dirname(loc), os.W_OK):
		raise Exception("Can't write to the specified location.")

def check_server_root(loc):
	"""Checks to make sure that the location given is valid and that the
	user has permission to write there."""
	loc = os.path.abspath(loc)
	# check if the name is good
	valid_chars = string.letters + string.digits + "/._"
	for char in loc:
		if char not in valid_chars:
			raise Exception("Invalid characters in location")
	# make sure you have write permissions there
	if not os.access(os.path.dirname(loc), os.W_OK):
		raise Exception("Can't write to the specified location.")
		
def get_keystore_location(tries_left=10):
	"""Gets the location at which the keystore will be located.

	Fails on the existence of a file/dir at that location, the inability to 
	write there, or a bad name.
	"""
	loc = ""
	# we only try so many times...
	for i in range(tries_left):
		try:
			loc = prompt("Please enter the desired keystore location: ")
			check_keystore_location(loc)
			break
		except Exception, e:
			logger.info(e)
	if loc: return loc
	raise Exception("Could not get location.")

def get_server_root(tries_left=10):
	"""Gets the location from which the server will be started.

	Fails on the inability to write to the location or a bad name.
	"""
	loc = ""
	# we only try so many times...
	for i in range(tries_left):
		try:
			loc = prompt("Please enter the server root location: ")
			check_server_root(loc)
			break
		except Exception, e:
			logger.info(e)
	if loc: return loc
	raise Exception("Could not get location.")

def get_days_till_expiration(s):
	expiration_date = datetime.datetime.strptime(s, "%m/%d/%Y")
	time_difference = expiration_date - datetime.datetime.now()
	return time_difference.days
	
def get_timeout_len():
	expiration_date = prompt("When would you like your certificates to expire? (mm/dd/yyyy) ")
	return get_days_till_expiration(expiration_date)

def get_project_location():
	return prompt("Please enter the location of the desired project: ")

def get_threshold(k):
	return prompt("Please enter the desired threshold for the %s role: " % k, int)

def build_root_cfg(root, timeout, keys):
	# construct the configuration file parser (hint: .ini)
	cp = ConfigParser()
	# handle the expiration data
	cp.add_section("expiration")
	cp.set("expiration", "days", timeout)
	cp.set("expiration", "years", 0)
	cp.set("expiration", "minutes", 0)
	cp.set("expiration", "hours", 0)
	cp.set("expiration", "seconds", 0)
	# build the role data
	for role in keys:
		cp.add_section(role)
		# each role has an associated list of key id's and a threshold
		key_ids, threshold = keys[role]
		# convert the key_ids stuff into a list it can read
		id_list = ",".join(key_ids)
		# and add that data to the appropriate section
		cp.set(role, "keyids", id_list)
		cp.set(role, "threshold", threshold)
	# we want to write this to <root>/root.cfg
	path = root + pathsep + "root.cfg"
	f = open(path, "w")
	cp.write(f)
	f.close()
	return path
		
def build_root_txt(location, fuzzy_keys, key_db, metadata_root):
	root_meta = signerlib.generate_root_meta(location, key_db)
	signed = signerlib.sign_meta(root_meta, fuzzy_keys, key_db)
	signerlib.write_metadata_file(signed, metadata_root + pathsep + "root.txt")
	
def build_targets_txt(target_root, fuzzy_keys, key_db, server_root):
	server_root = os.path.abspath(server_root)
	target_root = os.path.abspath(target_root)
	logger.info(target_root)
	metadata_root = os.path.join(server_root, "meta")
	cwd = os.getcwd()
	os.chdir(server_root)
	server_root_length = len(server_root)
	# get the list of targets
	targets = []
	for root, dirs, files in walk(target_root):
		for target_file in files:
			targets.append(os.path.join(root, target_file)[server_root_length+1:])
	# feed it to signerlib
	targets_meta = signerlib.generate_targets_meta(targets)
	# sign it
	signed = signerlib.sign_meta(targets_meta, fuzzy_keys, key_db)
	# write it
	signerlib.write_metadata_file(signed, metadata_root + pathsep + "targets.txt")
	os.chdir(cwd)

def build_release_txt(fuzzy_keys, key_db, metadata_root):
	release_meta = signerlib.generate_release_meta(metadata_root)
	signed = signerlib.sign_meta(release_meta, fuzzy_keys, key_db)
	signerlib.write_metadata_file(signed, metadata_root + pathsep + "release.txt")

def build_timestamp_txt(fuzzy_keys, key_db, metadata_root):
	release_path = metadata_root + pathsep + "release.txt"
	timestamp_meta = signerlib.generate_timestamp_meta(release_path)
	signed = signerlib.sign_meta(timestamp_meta, fuzzy_keys, key_db)
	signerlib.write_metadata_file(signed, metadata_root + pathsep + "timestamp.txt")

def update_metadata(keystore_path, project_root, root_cfg_path, server_dir, state=BUILD_ROOT):
	logger.info(state)
	# normalize the paths
	metadata_root = os.path.join(server_dir, "meta")
	targets_root = os.path.join(server_dir, "targets")

	# build the keydb
	key_db = keystore.KeyStore(keystore_path)
	if TEST: key_db.load(['test'])
	while True:
		if TEST: break
		line = signercli._get_password("Please input a decryption password for the keystore, or -- to stop: ")
		if line != '--':
			key_db.load([line])
		else:
			break

	# get the config data
	root_cfg = ConfigParser()
	root_cfg.read(root_cfg_path)
	fuzzy_root_keys = [key for key in root_cfg.get("root", "keyids").split(", ")]
	fuzzy_targets_keys = [key for key in root_cfg.get("targets", "keyids").split(", ")]
	fuzzy_release_keys = [key for key in root_cfg.get("release", "keyids").split(", ")]
	fuzzy_timestamp_keys = [key for key in root_cfg.get("timestamp", "keyids").split(", ")]
	
	# copy the project over to the targets root
	if project_root != targets_root:
		rmtree(targets_root)
		logger.info("removed the tree")
		copytree(project_root, targets_root)
		logger.info("copied the tree")

	# started
	if state == BUILD_ROOT:
		try:
			build_root_txt(root_cfg_path, fuzzy_root_keys, key_db, metadata_root)
			state += 1
		except:
			logger.info('Quickstart was unable to build root.txt. Please send the incomplete update to your root key holder.')
			logger.info('They can continue the update process by running quickstart with the \'-step build_root\' argument')
			state = FINISH
	# built_root
	logger.info("done with root")
	if state == BUILD_TARGETS:
		try:
			build_targets_txt(targets_root, fuzzy_targets_keys, key_db, server_dir)
			state += 1
			print("BUILT TARGETS")
		except:
			logger.info('Quickstart was unable to build targets.txt. Please send the incomplete update to your targets key holder.')
			logger.info('They can continue the update process by running quickstart with the \'-step build_targets\' argument')
			state = FINISH

	# built_targets
	logger.info("done with targets")
	if state == BUILD_RELEASE:
		try:
			build_release_txt(fuzzy_release_keys, key_db, metadata_root)
			state += 1
		except:
			logger.info('Quickstart was unable to build release.txt. Please send the incomplete update to your release key holder.')
			logger.info('They can continue the update process by running quickstart with the \'-step build_release\' argument')
			state = FINISH

	# built_release
	logger.info("done with the release")
	if state == BUILD_TIMESTAMP:
		try:
			build_timestamp_txt(fuzzy_timestamp_keys, key_db, metadata_root)
			state += 1
		except:
			logger.info('Quickstart was unable to build timestamp.txt. Please send the incomplete update to your timestamp key holder.')
			logger.info('They can continue the update process by running quickstart with the \'-step build_timestamp\' argument')
			state = FINISH

	# almost done
	logger.info("done with the timestamp")
	logger.info("done updating")

if __name__ == "__main__":

	global TEST

	import optparse

	parser = optparse.OptionParser()
	parser.add_option("-k", "--keystore", dest="KEYSTORE_LOCATION", default="")
	parser.add_option("--root_threshold", dest="ROOT_THRESHOLD", type=int, default=0)
	parser.add_option("--targets_threshold", dest="TARGETS_THRESHOLD", type=int, default=0)
	parser.add_option("--release_threshold", dest="RELEASE_THRESHOLD", type=int, default=0)
	parser.add_option("--timestamp_threshold", dest="TIMESTAMP_THRESHOLD", type=int, default=0)
	parser.add_option("-t", "--threshold", dest="DEFAULT_THRESHOLD", type=int, default=0)
	parser.add_option("-s", "--keysize", dest="DEFAULT_KEY_SIZE", default=2048)
	parser.add_option("-l", "--server_location", dest="SERVER_ROOT_LOCATION", default="")
	parser.add_option("-r", "--root", dest="PROJECT_ROOT_LOCATION", default="")
	parser.add_option("-e", "--expiration", dest="EXPIRE_DATE")
	parser.add_option("-v", dest="VERBOSE", type=int, default=0)
	parser.add_option("-u", dest="UPDATE", action="store_true")
	parser.add_option("-c", dest="CONFIG_PATH")
	parser.add_option("--step", dest="STATE", type=int, default=BUILD_ROOT)
	parser.add_option("--test", dest="TEST", action="store_true", default=False)

	options, args = parser.parse_args()

	if options.TEST:
		TEST = True

	# set the logging level
	if not options.VERBOSE == 0:
		set_log_level(logging.ERROR)
	elif options.VERBOSE == 1:
		set_log_level(logging.WARNING)
	elif options.VERBOSE == 2:
		set_log_level(logging.DEBUG)
	elif options.VERBOSE == 3:
		set_log_level(logging.INFO)

	if options.UPDATE:
		update_metadata(options.KEYSTORE_LOCATION,
				options.PROJECT_ROOT_LOCATION,
				options.CONFIG_PATH,
				options.SERVER_ROOT_LOCATION,
				options.STATE
				)
		exit(0)
	
	# handle the expiration time
	TIMEOUT = 0
	if options.EXPIRE_DATE:
		TIMEOUT = get_days_till_expiration(options.EXPIRE_DATE)
	
	# get the keystore location
	if not options.KEYSTORE_LOCATION:
		options.KEYSTORE_LOCATION = get_keystore_location()

	# build the keystore
	key_db = keystore.KeyStore(options.KEYSTORE_LOCATION)
	key_ids = {}
	for k in ["root", "targets", "release", "timestamp"]:
		threshold = getattr(options, k.upper() + "_THRESHOLD")
		if not threshold and not options.DEFAULT_THRESHOLD: 
			threshold = get_threshold(k)
		elif options.DEFAULT_THRESHOLD:
			threshold = options.DEFAULT_THRESHOLD
		for i in range(threshold):
			key = signerlib.generate_key(options.DEFAULT_KEY_SIZE)
			if TEST: password = 'test'
			else: password = signercli._get_password()
			key_db.add_key(key, password)
			try:
				key_ids[k][0].append(key.get_key_id())
			except KeyError:
				key_ids[k] = ([key.get_key_id()], threshold)
	key_db.save()

	# get the server root
	if not options.SERVER_ROOT_LOCATION:
		options.SERVER_ROOT_LOCATION = get_server_root()
	# build the server root
	metadata_loc = options.SERVER_ROOT_LOCATION + pathsep + "meta"
	print metadata_loc
	targets_loc = options.SERVER_ROOT_LOCATION + pathsep + "targets"
	print targets_loc
	try: mkdir(options.SERVER_ROOT_LOCATION)
	except: pass
	try: mkdir(metadata_loc)
	except: pass

	# get the timeout length
	if not TIMEOUT:
		TIMEOUT = get_timeout_len()
	# build root.cfg
	root_cfg_location = build_root_cfg(options.SERVER_ROOT_LOCATION, TIMEOUT, key_ids)

	# generate root.txt
	build_root_txt(root_cfg_location, key_ids["root"][0], key_db, metadata_loc)

	# get the project root
	if not options.PROJECT_ROOT_LOCATION:
		options.PROJECT_ROOT_LOCATION = get_project_location()	
	# copy it over
	tmp_dir = tempfile.mktemp()
	copytree(options.PROJECT_ROOT_LOCATION, tmp_dir)
	move(tmp_dir, targets_loc)

	# generate targets.txt
	build_targets_txt(targets_loc, key_ids["targets"][0], key_db, options.SERVER_ROOT_LOCATION)
	
	# generate release.txt
	build_release_txt(key_ids["release"][0], key_db, metadata_loc)
	
	# generate timestamp.txt
	build_timestamp_txt(key_ids["timestamp"][0], key_db, metadata_loc)
