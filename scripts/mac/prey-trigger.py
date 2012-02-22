#!/usr/bin/python2.5
# encoding: utf-8
#######################################################
# Prey Mac Network Trigger - (c) 2012 Fork Ltd.
# Written by Tomas Pollak <tomas@forkhq.com>
# Based on the SysConfig section of crankd.py
# Licensed under the GPLv3
#######################################################

# import signal
# import os
import sys
import shlex
# import logging
from subprocess import Popen, call, PIPE, STDOUT
from datetime import datetime, timedelta
from PyObjCTools import AppHelper
from getpass import getuser

from SystemConfiguration import \
	SCDynamicStoreCreate, \
	SCDynamicStoreCreateRunLoopSource, \
	SCDynamicStoreSetNotificationKeys

from Cocoa import \
	CFAbsoluteTimeGetCurrent, \
	CFRunLoopAddSource,  \
	CFRunLoopGetCurrent, \
	CFRunLoopAddTimer, \
	CFRunLoopTimerCreate, \
	NSRunLoop, \
	kCFRunLoopCommonModes
	
### run variables
debug = True
min_interval = 2 # minutes
# log_file = "/var/log/prey.log"
prey_command = "/usr/local/bin/prey"
command_env = {'TERM':'xterm', 'TRIGGER': 'true', 'USER': getuser()}

#try:
#	log_output = open(log_file, 'wb')
#except IOError:
#	print "No write access to " + log_file + ". Log output will go to /dev/null!"
#	log_output = open('/dev/null', 'w')

log_output = open('/dev/null', 'w')

#######################
# helpers
#######################

def connected():
	return interface_connected('en0') or interface_connected('en1')

def interface_connected(interface):
	try:
		x = call(["ipconfig", "getifaddr", interface], stdout=PIPE)
		# print(x)
		return x == 0
	except:
	 	return False

def log(message):
	print(message)
	if debug:
		shout(message, True)

# only for testing purposes
def shout(message, wait = False):
	args = shlex.split("osascript -e 'say \"" + message + "\"' using Zarvox")
	p = Popen(args)
	if wait:
		p.wait()

def run_prey():
	global run_at
	two_minutes = timedelta(minutes=min_interval)
	now = datetime.now()
	log("Welcome back master")
	if (run_at is None) or (now - run_at > two_minutes):
		log("The vulture has flown")
		try:
			p = Popen(prey_command, stdout=PIPE, stderr=PIPE, env=command_env)
			run_at = datetime.now()
			p.wait()
			log("Elvis has left the building")
		except OSError, e:
			print "\nWait a second! Seems we couldn't find Prey at " + prey_command
			print e
			sys.exit(1)

#######################
# event handlers
#######################

def network_state_changed(*args):
	# log("Holy shenanigans! Something's changed")
	if connected():
		run_prey()

def timer_callback(*args):
	"""Handles the timer events which we use simply to have the runloop run regularly. Currently this logs a timestamp for debugging purposes"""
	# logging.debug("timer callback at %s" % datetime.now())

#######################
# main
#######################

timer_interval = 2.0

if __name__ == '__main__':

	# log("Logging into the gibson")
	run_at = None
	if connected():
		run_prey()

	sc_keys = [
		'State:/Network/Global/IPv4',
		'State:/Network/Global/IPv6'
	]

	store = SCDynamicStoreCreate(None, "global-network-change", network_state_changed, None)
	SCDynamicStoreSetNotificationKeys(store, None, sc_keys)

	CFRunLoopAddSource(
		# NSRunLoop.currentRunLoop().getCFRunLoop(),
		CFRunLoopGetCurrent(),
		SCDynamicStoreCreateRunLoopSource(None, store, 0),
		kCFRunLoopCommonModes
	)

	# signal.signal(signal.SIGHUP, partial(quit, "SIGHUP received"))

	# NOTE: This timer is basically a kludge around the fact that we can't reliably get
	#       signals or Control-C inside a runloop. This wakes us up often enough to
	#       appear tolerably responsive:
	CFRunLoopAddTimer(
		NSRunLoop.currentRunLoop().getCFRunLoop(),
		CFRunLoopTimerCreate(None, CFAbsoluteTimeGetCurrent(), timer_interval, 0, 0, timer_callback, None),
		kCFRunLoopCommonModes
	)

	try:
		AppHelper.runConsoleEventLoop(installInterrupt=True)
	except KeyboardInterrupt:
		print "KeyboardInterrupt received, exiting"

	sys.exit(0)
