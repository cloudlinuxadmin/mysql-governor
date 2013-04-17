#!/usr/bin/python

import glob, os, shutil, stat, string
class CopyDirectory:
	def __init__ (self, source, destination, pattern="*", directorypattern ="*", overwriteolder=1, copyfile = shutil.copyfile):
		self.sourcedirectory = source
		self.destinationdirectory = destination
		self.pattern = pattern
		self.directorypattern = directorypattern
		self.overwriteolder = overwriteolder
		self.directorylist = []
		self.filelist = []
		self.copyfile = copyfile
	def process (self):
		print "Gathering file list"
		self.walk ()
		print "Building directory tree and copying files"
		self.go ()
	def walk (self):
		'''
		Gather the list of directories and files to copy
		'''
		os.path.walk(self.sourcedirectory, self._copydir, self )
	def go (self):
		'''
		Perform the primary function of copying a directory
		given an already constructed directory and file list
		(generally created by walk)
		'''
		for directory in self.directorylist:
			# following is built in to this class
			self.copydirectory (directory)
		for source, destination in self.filelist:
			print "%s --> %s"%(source, destination)
			# following is an argument to the constructor
			self.copyfile (source, destination)
	def _copydir( self, arg, directory, files):
		'''
		Perform copying for a particular directory
		'''
		#print directory
		# collect files, use files if we have '*' pattern
		workingfiles = self._files (directory, files)
		# filter subdirectories, modifies files in-place
		self._subdirectories (directory, files)
		destinationdirectory = self._directorysetup( directory )
		# should provide option for not overwriting files
		# possibly with date checks etc.
		# For extra marks, just collect this information
		# and return a list of copies to be made,
		# so the user can review before copying.
		# Do the copying
		#print workingfiles
		for file in workingfiles:
			source = os.path.join( directory, file)
			destination = os.path.join( destinationdirectory, file)
			if self.overwriteolder and os.path.exists( destination):
				if os.stat( source )[stat.ST_MTIME] > os.stat( destination )[stat.ST_MTIME]:
					# we don't care if it's older, or it is older (hopefully)
					self.filelist.append( (source, destination) )
				else:
					print "skip %s (source not newer)"%(source)
			else:
				self.filelist.append( (source, destination) )
	def _subdirectories ( self, directory, default):
		'''
		Filters the list of subdirectories which will be copied
		'''
		# following modifies which directories are copied
		# does so by modifying file list in place (see os.path.walk)
		if self.directorypattern != "*":
			default[:] = glob.glob( os.path.join( directory, self.directorypattern) )
	def _files( self, directory, default):
		'''
		create the filtered list of files
		'''
		def dirfilter( values,directory=directory):
			result = []
			for value in values:
				if not os.path.isdir( os.path.join( directory, value)):
					result.append( value)
			return result
		# following is for local processing
		if self.pattern != "*":
			return dirfilter( glob.glob( os.path.join( directory, self.pattern) ) )
		else:
			return dirfilter( default )
	def _directorysetup (self,directory):
		'''
		Ensure that the destination directory is available
		build it if it is not
		'''
		#print "setup directory", directory
		# should make this manipulation more robust
		# currently assumes all sorts of things :(
		prefix = os.path.commonprefix( (self.sourcedirectory, directory) )
		extendeddirectory = directory[len(prefix):]
		# get rid of preceding /, so won't be interpreted as root
		if extendeddirectory and extendeddirectory [0] == os.sep:
			extendeddirectory = extendeddirectory[1:]
		destinationdirectory = os.path.join (self.destinationdirectory, extendeddirectory)
		#print "  destinationdirectory", destinationdirectory
		self.directorylist.append( destinationdirectory)
		return destinationdirectory
	def copydirectory(self, directory):
		'''
		Called after tree building,
		creates needed directories
		'''
		# create directory if not already there
		#if not os.path.exists( directory ):
		try:
			os.mkdir( directory )
			print "made directory", directory
		except os.error:
			pass
