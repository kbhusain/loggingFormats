
#
# Modifications: 
#

#
# Adding capability to remove the motion to read grids if no decompression
#

######################################################
import sys 
import os
from struct import *
from string import strip, find, rfind, join, split, replace, upper
from os import chdir, getcwd
#from array import array
from time import time
import pickle
import errno
import profile
import copy
import operator
import numpy

class pECLwriter:
	def __init__(self):
		self.fmt_dynamicStr = '=' 
		self.fmt_singleLongStr = '=L'
		self.fmt_singleFloatStr = '=f'
		self.fmt_tripleLongStr = '=3L'
		self.fmt_5LongStr = '=5L'
		self.fmt_tripleFloatStr = '=3f'
		self.fmt_sevenLongStr = '=7L'
		self.fmt_8sL4sStr = '=8sL4s'
		self.fmt_24fStr = '=24f'
		self.fmt_header = '=L8sL4sL'

	def	getEndianness(self):
		return fmt_dynamicStr

	def setEndianness(self,useThis):
		self.fmt_dynamicStr = useThis
		if useThis == '<':  # Little Endian
			self.fmt_singleLongStr = '<L'
			self.fmt_singleFloatStr = '<f'
			self.fmt_tripleLongStr = '<3L'
			self.fmt_5LongStr = '<5L'
			self.fmt_tripleFloatStr = '<3f'
			self.fmt_sevenLongStr = '<7L'
			self.fmt_8sL4sStr = '<8sL4s'
			self.fmt_24fStr = '<24f'
			self.fmt_header = '<L8sL4sL'
			return 0
		else:
			self.fmt_singleLongStr = '>L'
			self.fmt_singleFloatStr = '>f'
			self.fmt_tripleLongStr = '>3L'
			self.fmt_5LongStr = '>5L'
			self.fmt_tripleFloatStr = '>3f'
			self.fmt_sevenLongStr = '>7L'
			self.fmt_8sL4sStr = '>8sL4s'
			self.fmt_24fStr = '>24f'
			self.fmt_header = '>L8sL4sL'
		return 1

	def writeECLrecord(self,fd,keyword,itype,nitems,items):
		"""
		fd must be opened in binary mode
		keyword must be exactly 8 characters long.
		itype   must be exactly 4 characters long.
		items   must be sent as string -  len = len(items)/4
		"""
		name = '%-8s' % keyword
		hdr = pack(self.fmt_header,16,name,nitems,itype,16)
		fd.write(hdr)
		#print keyword,nitems,len(items)
		fd.write(pack(self.fmt_singleLongStr,len(items)))
		if fmt_dynamicStr == '>':  # Big endian 
			fd.write(items)        # byteswap this string
		else:
			fd.write(items)        # as string
		fd.write(pack(self.fmt_singleLongStr,len(items)))


fmt_dynamicStr = '>' 
fmt_singleLongStr = '>L'
fmt_singleFloatStr = '>f'
fmt_tripleLongStr = '>3L'
fmt_5LongStr = '>5L'
fmt_tripleFloatStr = '>3f'
fmt_sevenLongStr = '>7L'
fmt_8sL4sStr = '>8sL4s'
fmt_24fStr = '>24f'


def setEndiannessOnFile(filename,obj=None):
	global fmt_dynamicStr 
	try:
		dr = open(filename,'rb')			 # Check if cache exists.
	except:
		print "Unable to open : ", filename 
		return -1
	w = dr.read(4)   # Read
	wl=unpack('L',w)
	dr.close()
	if wl[0] == 16: 
		if obj <> None: obj.dataOrder    = 'little'
		setEndianness('<')
	else:
		if obj <> None: obj.dataOrder    = 'big'
		setEndianness('>')
	return 1

def setEndianness(useThis):
	global fmt_dynamicStr 
	global fmt_singleLongStr
	global fmt_singleFloatStr
	global fmt_tripleLongStr
	global fmt_5LongStr
	global fmt_tripleFloatStr 
	global fmt_sevenLongStr 
	global fmt_8sL4sStr 
	global fmt_24fStr 
	global fmt_header 
	fmt_dynamicStr = useThis
	if useThis == '<':
		fmt_singleLongStr = '<L'
		fmt_singleFloatStr = '<f'
		fmt_tripleLongStr = '<3L'
		fmt_5LongStr = '<5L'
		fmt_tripleFloatStr = '<3f'
		fmt_sevenLongStr = '<7L'
		fmt_8sL4sStr = '<8sL4s'
		fmt_24fStr = '<24f'
		fmt_header = '<L8sL4sL'
	else:
		fmt_singleLongStr = '>L'
		fmt_singleFloatStr = '>f'
		fmt_tripleLongStr = '>3L'
		fmt_5LongStr = '>5L'
		fmt_tripleFloatStr = '>3f'
		fmt_sevenLongStr = '>7L'
		fmt_8sL4sStr = '>8sL4s'
		fmt_24fStr = '>24f'
		fmt_header = '>L8sL4sL'
		return 1
	return 0

######################################################
# Very simple class specifically for the GRID class.
# Does not work. USE WITH CARE... 
######################################################
class bufferedInput:
	def __init__(self,fd=None):
		""" fd must be opened as rb """
		self.fd = fd
		self.buffer = None
		self.index = 0
		self.bufferSize = 1024000     # This is fixed. 
		self.bytesLeft  = 0

	def doSeek(self,fd,n,whence=1):
		"""  seeks from start of file """
		if (self.bytesLeft >= n): 
			k  = self.index + n
			self.bytesLeft -= n
			return
		n = n - self.bytesLeft
		self.bytesLeft = 0
		self.buffer = None
		fd.seek(n,1)

	def doRead(self,fd,n):
		""" returns a string with up to n bytes """	
		if (self.bytesLeft >= n): 
			self.bytesLeft -= n
			return self.buffer[self.index:self.index+n]
		ret = ''
		if self.buffer <> None:
			ret = self.buffer[self.index:]     # return copy
		n = n - self.bytesLeft
		self.buffer=fd.read(self.bufferSize) # read next chunk
		self.bytesLeft = len(self.buffer)
		self.bytesLeft -= n
		self.index = 0 
		ret = ret + (self.buffer[0:self.index + n])
		return ret
			

######################################################
#  This is repeated in the PBFutils package.
######################################################
class uBufferedFORTRANRecord:
	""" The basic FORTRAN record block is read here """
	def __init__(self):
		self.incoming = 0  # temp variable.
		self.item = ''     # The item itself.
		self.bufferer = bufferedInput()
		self.location = 0

	def readRecord(self,fd,skip=0,frombytes=0,numbytes=-1):
		""" 
		You must pass in a file descriptor to a file
		that is opened in binary mode (rb) located at the 
		start of first byte of record 
		"""
		inc = fd.read(4)   # Read start block size.
		if (len(inc) == 0): return 0
		bufb = unpack(fmt_singleLongStr,inc)
		szb = bufb[0]
		self.location = fd.tell()    # After reading the four bytes
		#print "Location = %d, %x " % (self.location, szb)
		if (skip == 1):
			fd.seek(szb+4,1)
			return szb
		if (numbytes > 0):
			#print "Location %d %d  szb %d pECLutils.py \n" % (self.location, bufb[0], szb)
			fd.seek(self.location+frombytes)
			self.item = fd.read(numbytes)   # NOTE this this in bytes
			fd.seek(self.location+szb+4)    # Return
			#print "Location: %d - %d" % (self.location+szb+4, len(self.item))
			return szb
		self.item = fd.read(szb) # skip forward.
		####self.item = self.bufferer.doRead(fd,szb)   # Read start block size.
		if (len(self.item) <> szb):
			print "From ", frombytes, " read ", numbytes, " from ", self.location
			print "Could not read %x bytes at  line 100: pECLutils.py " % (szb)
			print "Read  ", len(self.item) , " instead"
			#print "fmt long str = ", fmt_singleLongStr 
			return 0
		###inc = self.bufferer.doRead(fd,4)   # Read start block size.
		inc = fd.read(4)   # Read end block size
		if (len(inc) == 0): 
			print "Could not read at  line 38: pECLutils.py "
			return 0
		sze = unpack(fmt_singleLongStr,inc)
		if (sze[0] <> szb):
			print "SEVERE DATA ERROR!! block sizes incorrect %d,%d" % (self.sze, szb)
		# print szb,"<<<<block>>>>", self.sze
		return szb 

######################################################
#
######################################################
class uECLHeader(uBufferedFORTRANRecord):
	""" Encapsulates an ECL header: 
	8 character keyword + size in units of items to follow. """
	def __init__(self):
		self.incoming = 0  # temp variable.
		self.item = ''     # The item itself.
		self.bufferer = bufferedInput()
		pass

	def parseHead(self):
		[self.keyword,self.iItemCount,self.iType] = unpack(fmt_8sL4sStr,self.item);
		#print "ParseHead", len(self.item), fmt_8sL4sStr, self.keyword,self.iItemCount
		if ((self.iType == 'DOUB') or (self.iType == 'CHAR')):
			self.iDataSize = self.iItemCount * 8
		else: 
			self.iDataSize = self.iItemCount * 4

	def dumpAsText(self): 
		print "\n'%8s' %d '%s'" % (self.keyword,self.iItemCount,self.iType)

#######################################################################
#
#######################################################################
class eclWellClass:
	def __init__(self,name=''):
		self.name = name
		self.points = [] 
		self.coordinates = []
		self.keyxyz = {}

	def appendIJK(self,ijk):
		self.points.append(ijk)

	def mapIJKtoXYZ(self,xArray,yArray,depths):
		nx = len(xArray)
		ny = len(yArray)
		nxy = nx * ny
		#print "nx ",nx,"ny ",ny, "nxy", nxy, "depth = ", len(depths)
		self.coordinates = []
		self.keyxyz = {}
		for i,j,k in self.points:
			x = xArray[i-1]
			y = yArray[j-1] * -1                 # For some bizzarre reason....
			index = (k-1) * nxy + (j-1) * nx + i - 1
			#print self.name,i-1,j-1,k-1
			z = depths[index]
			akey = str(x) + ":" + str(y) + ":" +  str(z)
			if not self.keyxyz.has_key(akey):
				self.keyxyz[akey] = 1
				self.coordinates.append([x,y,z])


#######################################################################
#  This is used to track independant INTEHEAD object.
#######################################################################
class basicINTEHEADobject:
	"""
	Encapsulates each INTEHEAD object in the UNRST or INIT file.
	The variable names follow the ECLIPS standard.
	"""
	def __init__(self):
		self.nx = 0 
		self.ny = 0 
		self.nz = 0 
		self.count = 0
		self.nactiv = 0
		self.nwell = 0			# [16] no. of wells. 
		self.nzwel = 0 			# [27] no. of 8 char blocks per well name
		self.ncwma  = 0			# [17] max completions per well
		self.nicon  = 0			# [32] connections per well
		self.m_wells = []  #
		self.setDate(1970,1,1)

		self.lgrIndex = -1
		self.seqNum   = 0 

	def getDate(self):
		return self.dateString

	def setDate(self,yr,mo,dy):
		self.month = mo 
		self.day   = dy 
		self.year  = yr
		self.dateString = "%04d-%02d-%02d" % (self.year,self.month,self.day)

	def setDimensions(self,x,y,z,a):
		self.nx = x 
		self.ny = y 
		self.nz = z 
		self.count = x * y * z 
		self.nactiv = a 

	def getDimensionString(self):
		xxstr = "%d x %d x %d  with %d active" % (self.nx,self.ny,self.nz,self.nactiv)
		return xxstr

	def getQuickInfoStrings(self):
		xxstr = "%d x %d x %d [%d]  with %d active cells " % (self.nx,self.ny,self.nz,self.count,self.nactiv)
		xxstr = xxstr + '\nDate= ' + self.dateString
		xxstr = xxstr + '\nWell Count   = ' + str(self.nwell) + '\n'
		xxstr = xxstr + '\nCompletions  = ' + str(self.ncwma) + '\n'
		return xxstr


	def createRecord(self):
		items = numpy.zeros(96,'l')
		items[2] = 1
		items[8] = self.nx
		items[9] = self.ny
		items[10] = self.nz
		items[11] = self.nactiv           # NACTIV
		items[14] = 3                     # NPHASE
		items[64] = self.day
		items[65] = self.month
		items[66] = self.year
		items[94] = 300
		return items
		#return pack('>96I',items)

	
######################################################
# This contains an item too. 
######################################################
class uECLRecord:
	def __init__(self):
		self.eclHead = uECLHeader();
		self.eclData = uBufferedFORTRANRecord();
		self.fromhere = 0 
		self.skipList = []  # Dynamically created; list of records to ski


	def readDirectRecord(self,fd,recstart,offset,numbytes):
		"""
		The file must be seeked to start of the record.
		"""
		fd.seek(recstart+28+offset,0)      #Go to location of data
		return fd.read(numbytes)
		

	def readECLrecord(self,fd,rsize=-1,frombytes=0,numbytes=-1,recname=None):
		"""
		The fully constructed data is returned in the .item member.
		The eclHead.item structure contains the head information which 
		can be unpacked with ">8sL4s" for the (name, itemCount, type)
		Do NOT use the eclData.item object of this record. It is used
		to store the reads per block as the .item is constructed. 
		There is no guarantee that the len(self.item) == len(self.eclData.item) !!

		There are three ways to use the rsize parameter to your advantage.
		if rsize <= -1; read record 
		if rsize == 0 : read header only so it's much faster.
		else read record only if itemsize == dataItemSize

		"""
		self.fromhere = fd.tell()             #Start of the record Header
		#print "Read From Here", self.fromhere
		r1 = self.eclHead.readRecord(fd)      #incoming contains header.
		if (r1 < 1): return -1                #End of file is reached 
		self.eclHead.parseHead()              #set up internal
		self.item = ''                        # Name does not match, return empty.
		if (numbytes > 0):                    #:w
			if (self.eclHead.keyword==recname) or (recname==None): 
				self.eclData.readRecord(fd,skip=0,frombytes=frombytes,numbytes=numbytes)   
				self.item = self.eclData.item
				#print "Return ", len(self.eclData.item) # read only this data.
			else: 
				self.eclData.readRecord(fd,skip=1) # Skip the record.
			return 1
		keyword = strip(self.eclHead.keyword) #Get the keyword not.
		skipFlag = 0 					      #Don't skip 
		if rsize == 0: skipFlag = 1           #Skip if requested size = 0
		if keyword=='INTEHEAD': skipFlag = 0  #but always read INTEHEAD even if skipping
		if keyword in self.skipList: skipFlag =1 # Honor the skip list.
		r3 = self.eclHead.iDataSize              # get number of items.

		self.item = '' 
		while (r3 > 0):
			if rsize == -1 or skipFlag == 0:       # Must read record
				r2 = self.eclData.readRecord(fd)   # read the whole mess
				if (r2 < 1): return -1
				self.item = self.item + self.eclData.item
			else:
				if (rsize > 0 and rsize <> self.eclHead.iDataSize) or rsize == 0:
					r2 = self.eclData.readRecord(fd,1) #Skip it.
				else:		
					r2 = self.eclData.readRecord(fd)   #Read it, it matches 
					if (r2 > 0): 
						self.item = self.item + self.eclData.item
			r3 = r3 - r2 
			# print fd.tell()
		#if rsize == self.eclHead.iDataSize: 
		#if keyword=='PARAMS': print "Return self.item with", len(self.item)
		return 1

	def listECLrecord(self,fd):
		"""
		Dummy function which reads the ecl header only and skips past the data.
		"""
		return self.readECLrecord(fd,0)

	def dumpRecord(self):
		""" 
		Dumps the contents of an ECL record as text for the 
		the following records: DIMENS, GRIDUNIT, RADIAL, COORDS
		Works in UNIX only. 
		Needs work for detailed report generation.
		"""
		if self.eclHead.keyword == "DIMENS  ":
			fmtstr = str(self.eclHead.iItemCount) + 'L'
			print unpack(fmtstr,self.eclData.item)
		if self.eclHead.keyword == "GRIDUNIT":
			print self.eclData.item
		if self.eclHead.keyword == "RADIAL  ":
			print self.eclData.item
		if self.eclHead.keyword == "COORDS  ":
			[ix,iy,iz,cn,active,hn,cc] = unpack(fmt_sevenLongStr,self.eclData.item)
			print ix,iy,iz,cn,active,hn,cc
		if self.eclHead.keyword == "CORNERS ":
			corners = unpack(fmt_24fStr,self.eclData.item)
			print corners

	def dumpAsText(self): 
		self.eclHead.dumpAsText()
		#
		# Based on the of header, print out the data ...
		# 
		iIndex = 0
		iCount = 0
		if self.eclHead.iType == 'INTE':
			data = numpy.array('i')
			data.fromstring(self.eclData.item)
			if sys.byteorder == 'little': data = data.byteswapped()  # if on Intel
			xlen = len(data)

			while iIndex < xlen:
				iCount=iCount + 1
				print " %11d" % data[iIndex] ,
				if iCount > 5: print " " * 7; iCount = 0
				iIndex=iIndex + 1

		elif self.eclHead.iType == 'REAL':
			data = numpy.array('f')
			data.fromstring(self.eclData.item)
			if sys.byteorder == 'little': data = data.byteswapped()  # if on Intel
			xlen = len(data)
			if xlen <> self.eclHead.iItemCount:
				print "__________ %d .., %d, srcCt=%d" % (xlen,self.eclHead.iItemCount,len(self.eclData.item))
			while iIndex< xlen:
				iCount=iCount + 1
				print " %16.8f" % data[iIndex],
				if iCount > 3: print " " * 11 ; iCount = 0
				iIndex=iIndex + 1
			if iIndex <> self.eclHead.iItemCount:
				print "__________ %d .., %d" % (xlen,self.eclHead.iItemCount)
		elif self.eclHead.iType == 'DOUB':
			data = numpy.array('d')
			data.fromstring(self.eclData.item)
			if sys.byteorder == 'little': data = data.byteswapped()  # if on Intel
			xlen = len(data)
			while iIndex< xlen:
				iCount=iCount + 1
				print " %22.14g" % data[iIndex],
				if iCount > 2: print " " * 13; iCount = 0
				iIndex=iIndex + 1
		elif self.eclHead.iType == 'LOGI':
			data = numpy.array('i')
			data.fromstring(self.eclData.item)
			if sys.byteorder == 'little': data = data.byteswapped()  # if on Intel
			xlen = len(data)
			while iIndex< xlen:
				iCount=iCount + 1
				if data[iIndex] == 0: 
					print " F",
				else: 
					print " T",
				if iCount > 24: print " " * 4; iCount = 0
				iIndex=iIndex + 1
		elif self.eclHead.iType == 'CHAR':
			while iIndex < xlen:
				print "  %8s" % data[iIndex:iIndex+8]
				iCount = iCount + 8
				if iCount > 6: print " " * 3; iCount = 0
				iIndex = iIndex + 8
		
######################################################
# 
######################################################
class basicECLfile:
	def __init__(self):
		self.verbose = 0
		self.errors   = []
		self.m_INTEHEADarray= []          # Keep a list of the INTEHEAD records.
		self.m_INTEHEADsizes= []          # Keep a list of sizes of the INTEHEAD records.
		self.m_LGRNAMES     = []          # If any LGRs, then names are padded 8 characters.
		self.m_SEQNUMS      = []          # Index of time steps in an UNRST file.
		self.m_PORVarray    = []          # Keep a list of all PORV arrays.
		self.m_IWELLarray= []             #to keep a list of the IWELL path records.
		self.m_yr = 1940
		self.m_mo = 1
		self.m_dy = 1
		self.lastIndexFetched = -1; 
		self.lastArrayFetched = numpy.array([],'f')  # place holder.
		self.arrayTypeCodes = {'DOUB':'d','REAL':'f','INTE':'i','LOGI':'i'}
		self.workingDir = os.getcwd()
		self.filename = None
		self._fd = None
		self.dataType = 'GRID'  # This must be set before opening the file 
		self.dataOrder= 'big'
		self.bogusNames = ['SEQNUM','INTEHEAD','LOGIHEAD', 'DOUBHEAD', 'IGRP',
			'IWEL', 'ISEG', 'NWEL', 'ZWEL', 'ICON', 'HIDDEN', 'ZTRACER', 
			'LGRNAMES', 'LGR', 'LGRHEADI', 'LGRHEADQ']

	def readHeader(self,whence=None):
		pass

	def openFile(self,ofile):
		print "Opening file", ofile, " and ", self.filename
		if self.filename == ofile: return
		self.filename = ofile
		lindex = self.filename.rfind('/')
		self.fileprefix = self.filename[lindex:]
		############################# Check for index ###########	
		(filepath,filename) = os.path.split(ofile)
		(shortname,bigextension) = os.path.splitext(filename)
		if len(filepath) < 1: filepath=os.getcwd()
		setEndiannessOnFile(self.filename,self)
		tempDirName=os.getenv('RS3DTEMP')
		if tempDirName == None:
			if os.name == 'nt':
				tempDirName = 'C:/temp/' 
			else:
				try:
					tempDirName = filepath + os.sep
					print "THIS IS THE FIRST XXX CACHE: [%s]" %(tempDirName)
					fd = open(filepath+os.sep+'t.txt','w')
					fd.close()
				except:
					print "Exception IS THE FIRST XXX CACHE:", tempDirName
					tempDirName = os.getenv('HOME') + os.sep
		self.cachename = tempDirName +  shortname + bigextension + ".ndx"
		print "THIS IS THE SECOND XXX CACHE:", self.cachename
		try:
			lstat = os.stat(ofile)
			cstat = os.stat(self.cachename)
			cacheTime = cstat[-1] - lstat[-1]
		except:
			cacheTime = -1

		self.records = []
		stime = time()
		a = self.checkCache() 
		if a == 0 or cacheTime < 0:
			dr = open(self.filename,'rb')			 # Check if cache exists.
			tempDirName=os.getenv('RS3DTEMP')
			if tempDirName == None:
				if os.name == 'nt':
					tempDirName = 'C:/temp/' 
				else:
					tempDirName = os.getenv('HOME') + os.sep
			#self.cachename = tempDirName +  shortname + bigextension + ".ndx"
			cachefile = open(self.cachename,'w')
			#print "Creating cache [2 min. per GIG  time required] ... for ",   self.cachename
			cachefile.write('#source file=%s\n' % self.filename )

			seqRecord = None
			seqString = ''
			fr = uECLRecord()
			# print fmt_singleLongStr
			retCount = fr.listECLrecord(dr)
			while (retCount> 0):
				s = strip(fr.eclHead.keyword)
				if s == 'SEQNUM': seqRecord = copy.copy(fr)
				if s == 'INTEHEAD':
					front = fr.item[256:268]  # for the time stamp
					nitems = unpack(fmt_tripleLongStr,front)
					self.m_yr = nitems[2]
					self.m_mo = nitems[1]
					self.m_dy = nitems[0]
					# print s
				if s == 'INTEHEAD' and seqRecord <> None: 
					seqString = "SEQNUM 1 INTE %d %04d-%02d-%02d\n" %  \
						(seqRecord.fromhere,self.m_yr,self.m_mo,self.m_dy)
						#(seqRecord.eclHead.iItemCount,seqRecord.eclHead.iType,
					cachefile.write(seqString)
					seqRecord = None
				str = "%s %d %s %d %04d-%02d-%02d\n" %  (s,fr.eclHead.iItemCount,\
					fr.eclHead.iType, fr.fromhere, self.m_yr,self.m_mo,self.m_dy)
				if s <> 'SEQNUM': cachefile.write(str)   # Defer writing sequence numbers
				retCount = fr.listECLrecord(dr)
			dr.close()
			cachefile.write("ENDOFCACHE\n")
			cachefile.close()
			if self.verbose ==1 : print "done with creating cache ", time() - stime, " seconds " 

		################### Try reading again ###############
		a = self.checkCache() 
		if a == 0: 		# Now try 
			if self.verbose ==1 : print "Unable to read created Cache!!! Severe Error"
			return -1 

		dr = None
		try:							   # Read the file.
			dr = open(ofile,'rb')
		except:
			print "Unable to open file to read.", ofile
			return -1	

		if dr <> None:
			self._fd = dr
			self.readINTEHEADarray(dr)	   #
			if self.dataType == 'INIT':    #
				self.readPORVarray(dr) 	   # For unified restart files, this will be 0
			if self.dataType == 'UNRST':   #
				#print "Reading Wells and Icons "
				self.readWELLarray(dr)	   #
				self.readICONarray(dr)	   # Read connections
			return 0					   # All is OK	
			#dr.close()
		return -1

	def closeFile(self):
		try:
			self._fd.close()
		except:
			print "closing file", self.filename 

	def getAttrNames(self):
		"""
		Returns a list of all the attributes to be used in drop
		down lists. Each entry in the returned array has 
		the form: name size [date]
		"""
		names = []
		for n in self.records:
			xstr = n[0] + " " +  n[4] + " [" + str(n[1]) + "]" 
			names.append(xstr)
		names.sort()
		return names

	#########################################################
	def getNamesAndDates(self):
		names = []
		for n in self.records:
			xstr = n[0] + " [" + str(n[4]) + "]" 
			names.append(xstr)
		return names

	#########################################################
	def getNamesForSearching(self, removeBogus=0):
		names = []
		k = 0
		for n in self.records:
			nm = n[0]
			if removeBogus == 0:
				xstr = n[0] +  " " + str(n[4]) + ' ' + str(k)
				names.append(xstr)
			else:
				if not nm in self.bogusNames and not nm in names: 
					xstr = n[0] +  " " + str(n[4]) + ' ' + str(k)
					names.append(xstr)
			k = k + 1
		return names

	#########################################################
	# These are the attr names from the cache. ...
	#########################################################
	def getNames(self,removeBogus=0):
		names = []
		for n in self.records:
			nm = n[0]
			if removeBogus == 0:
				names.append(nm)
			else:
				if not nm in self.bogusNames and not nm in names: 
					names.append(nm)
		return names

	#########################################################
	def getNameOfRecord(self,i):
		if i < len(self.records):
			n = self.records[i]
			return n[0]
		return "None"

	#########################################################
	def getDimensionString(self):
		names = ['Records   ,  Size   , Type']
		for n in self.records:
			str = n[0] +  "," + str(n[1])  + "," + n[2]  + "\n"
			names.append(str)
		return names

	
	#########################################################
	# If cache is found, read it. 
	# Return 1 if all ok. Return 0 if any error or not found.
	# Check integrity with the ENDOFCACHE on last line. 
	#########################################################
	def checkCache(self):
		found = 0
		try:
			ifile = open(self.cachename,'rb')
		except:
			return 0	
		self.records = []
		instr = ifile.readline()
		while(instr):
			if instr[0] == '#': 
				instr = ifile.readline()
				continue
			ilist = split(instr)
			k = instr.find("ENDOFCACHE") 
			if (k == 0):
				found = 1
				break;
			record = (ilist[0],int(ilist[1]),ilist[2],long(ilist[3]),ilist[4])
			self.records.append(record)
			ilist = split(instr)
			instr = ifile.readline()
			k = instr.find("ENDOFCACHE") 
			if (k == 0):
				found = 1
				break;
		ifile.close()
		if found == 0: self.records = []
		return found 


	##########################################################################
	def readINTEHEADarray(self,dr):
		"""
		Reads the integer head arrays and overwrites existing arrays.
		"""
		fr = uECLRecord()
		self.m_INTEHEADarray= []           #to keep a list of the INTEHEAD records.
		self.m_INTEHEADsizes=[]
		self.m_LGRNAMES =[]
		seqNum   = -1 
		lgrIndex = -1 

		for n in self.records:
			if (find(n[0],'LGRNAMES') == 0):
				dr.seek(n[3],0)              # seek to record.
				fr.readECLrecord(dr)         # item contains all LGRnames.
				count = int(n[1])
				k = 0 
				for i in range(count):
					name = unpack('8s',fr.item[k:k+8])
					k = k + 8
					self.m_LGRNAMES.append(strip(name[0]))
				break;

		#if len(self.m_LGRNAMES ) > 0: 
			#print " I have found " , len(self.m_LGRNAMES), " lgrs " 
			#print " They are " , self.m_LGRNAMES

		lastSequence  = None
		self.lastDate = None
		for n in self.records:
			if (find(n[0],'SEQNUM') == 0):   # This will let you 
				seqNum = seqNum + 1
				lgrIndex = -1
				
				continue
			if (find(n[0],'LGR') == 0) and (find(n[2],'CHAR') == 0 ) :
				lgrIndex = lgrIndex + 1
				continue
			if (find(n[0],'INTEHEAD') == 0):
				dr.seek(n[3],0) # seek to record.
				fr.readECLrecord(dr)  # item contains data.
				ml = 33
				fmtstr = fmt_dynamicStr + "%dL"  % ml  # Check the top of the file. 
				front =  fr.item[0:ml*4]      # first 16 integers.
				nitems = unpack(fmtstr,front)  # unpack to local machine 
				header = basicINTEHEADobject() #

				header.seqNum    = seqNum              # July 5,2004
				header.lgrIndex  = lgrIndex            # July 5,2004

				header.setDimensions(nitems[8],nitems[9],nitems[10],nitems[11])      # sets nactiv too.
				# print "Dimensions = ", (nitems[8],nitems[9],nitems[10],nitems[11])
				header.nwell  = nitems[16] 			  # No. of wells
				header.nzwel  = int(nitems[27]) * 8   # No. of chars per well name
				header.ncwma  = nitems[17] 			  # Max completions per well
				header.nicon  = nitems[32]			  # Data elements per connection in well
				#print "Wells = %d x %d = %d , %d" % (nitems[16],nitems[24], nitems[16] * nitems[24], nitems[27])
				# print nitems
				front = fr.item[256:268]  # Get the date integers
				nitems = unpack(fmt_tripleLongStr,front)
				header.setDate(nitems[2],nitems[1],nitems[0])
				# KAMRAN - MAY 7, 2005 - Removed adding SEQNUM if INTEHEAD found.
				self.lastDate = header.dateString
				self.m_SEQNUMS.append(self.lastDate)

				# if lgrIndex == -1: self.m_SEQNUMS.append(header.dateString)   # Only for full blocks...
 				self.m_INTEHEADarray.append(header)
				#if not header.count in self.m_INTEHEADsizes:
					#self.m_INTEHEADsizes.append(header.count)
				if not header.nactiv in self.m_INTEHEADsizes:
					self.m_INTEHEADsizes.append(header.nactiv)
		if self.verbose == 1:
			print " I have found " , lgrIndex , " LGR records"
			print " I have found " , len(self.m_SEQNUMS), " sequences " 
		#for m in self.m_SEQNUMS: print m

	def getFILEHEADasText(self,nitems,asList=0):
		olist = []
		olist.append('VERSION  = %d\n' % nitems[0])
		olist.append('RELEASE YR = %d\n' %(nitems[1]))
		if nitems[4] == 0: olist.append('CORNER POINT\n')
		if nitems[4] == 1: olist.append( 'UNSTRUCTURED\n')
		if nitems[4] == 2: olist.append( 'HYBRID GEOMETRY\n')
		if nitems[5] == 0: olist.append( 'SINGLE POROSITY\n')
		if nitems[5] == 1: olist.append( 'DUAL POROSITYn')
		if nitems[5] == 2: olist.append( 'DUAL PERMEABILITY\n')
		if asList == 1: return olist
		return "".join(olist)

	def getGRIDHEADasText(self,nitems,asList=0):
		olist = []
		if nitems[0] == 2: olist.append( 'UNSTRUCTURED\n')
		if nitems[0] == 1: olist.append( 'CORNER POINT\n')
		if nitems[0] == 0: olist.append( 'COMPOSITE\n')
		olist.append( 'NX = %d\nNY = %d\nNZ = %d\nLGR INDEX=%d\n'  \
			% (nitems[1],nitems[2],nitems[3],nitems[4]))
		olist.append( 'MODELSIZE  = %d\n' % (nitems[1] * nitems[2] * nitems[3]))
		olist.append( 'NUMRES = %d\nNSEG = %d\nNTHETA = %d\n' %(nitems[24],nitems[25],nitems[26]))
		olist.append( 'LOWER POINT I = %d  J = %d  K = %d\n' %(nitems[27],nitems[28],nitems[29]))
		olist.append( 'UPPER POINT I = %d  J = %d  K = %d\n' %(nitems[30],nitems[31],nitems[32]))
		
		if asList == 1: return olist
		return "".join(olist)

	def getINTEHEADasText(self,nitems,asList=0):
		olist = []
		olist.append('INTEHEAD\nSEQNUM = %d\n' % nitems[1])
		units = nitems[2]
		if units == 1: olist.append('UNITS: (%d) METRIC\n' % units)
		if units == 2: olist.append('UNITS: (%d) FIELD\n' % units)
		if units == 3: olist.append('UNITS: (%d) LAB\n' % units)
		olist.append( 'NX = %d\nNY = %d\nNZ = %d\nNACTIV = %d\n' \
			%(nitems[8],nitems[9],nitems[10],nitems[11]))
		olist.append( 'MODELSIZE  = %d\n' % (nitems[8] * nitems[9] * nitems[10]))
		iphs = nitems[14]
		if iphs == 1: olist.append('PHASE: (%d) OIL\n' % iphs)
		if iphs == 2: olist.append('PHASE: (%d) WATER\n' % iphs)
		if iphs == 3: olist.append('PHASE: (%d) OIL/WATER\n' % iphs)
		if iphs == 4: olist.append('PHASE: (%d) GAS\n' % iphs)
		if iphs == 5: olist.append('PHASE: (%d) OIL/GAS\n' % iphs)
		if iphs == 6: olist.append('PHASE: (%d) GAS/WATER\n' % iphs)
		if iphs == 7: olist.append('PHASE: (%d) OIL/GAS/WATER\n' % iphs)

		nwell = nitems[16]
		niwel = nitems[24]
		nzwel = nitems[27]
		ncwma = nitems[17]
		nicon = nitems[32]
		nwgmax = nitems[19]
		ngmaxz = nitems[20]
	
		if len(nitems) >= 178: 
			nswlmx = nitems[175]
			nsegmx = nitems[176]
			nisegz = nitems[178]
		else:
			nswlmx = 0
			nsegmx = 0
			nisegz = 0

	
		olist.append( 'NWELL = %d\nNCWMA = %d, NWGMAX = %d, NGMAXZ = %d\n' % (nwell,ncwma,nwgmax,ngmaxz))
		olist.append( 'NIWELL = %d, NZWELL = %d, NICON = %d\n' % (niwel,nzwel,nicon))
		olist.append( 'ICON count = %d\n' % (nwell * ncwma * nicon ))
		olist.append( 'IWEL count = %d\n' % (niwel * nwell ))
		olist.append( 'DAY = %d MONTH = %d YEAR = %d\n' % (nitems[64],nitems[65],nitems[66]))
		olist.append( 'NSWLMX = %d, NSEGMX = %d, NISEGZ = %d\n'  % (nswlmx,nsegmx,nisegz))
		olist.append( 'ISEG count =  %d\n'  % (nswlmx * nsegmx * nisegz))
		olist.append( 'ECLIPSE %d\n%s\n' % (nitems[95],'-'*30))

		if asList == 1: return olist
		return "".join(olist)

	##########################################################################
	def readWELLarray(self,dr):
		fr = uECLRecord()
		inteIndex = 0
		for n in self.records:
			if (find(n[0],'ZWEL') == 0):
				dr.seek(n[3],0) # seek to record.
				fr.readECLrecord(dr)                      # item contains data.
				inteObj = self.m_INTEHEADarray[inteIndex]
				# print "inteObj.nzwel = ", inteObj.nzwel 
				m = 0
				for k in range(inteObj.nwell):
					name = fr.item[m: m + inteObj.nzwel ]
					m = m+inteObj.nzwel
					well	= eclWellClass(name)
					#print "Adding ... ", name, m, 
					inteObj.m_wells.append(well)
				inteIndex = inteIndex + 1

	##########################################################################
	def readICONarray(self,dr):
		#print "read .. ico array"
		fr = uECLRecord()
		inteIndex = 0
		for n in self.records:
			if (find(n[0],'ICON') == 0):
				dr.seek(n[3],0) # seek to record.
				fr.readECLrecord(dr)                     # item contains data.
				inteObj = self.m_INTEHEADarray[inteIndex]
				z = 0
				s = 0
				sz = inteObj.nicon * 4
				fmtstr = fmt_dynamicStr + '%dL' % (inteObj.nicon)
				while z < inteObj.nwell:
					well = inteObj.m_wells[z]
					pt = 0
					while pt < inteObj.ncwma: 
						blob = fr.item[s:s+sz]
						items = unpack(fmtstr,blob)
						if (items[1] <> 0): 
							well.appendIJK((items[1],items[2],items[3]))
						s = s+sz	
						pt = pt+1
					z = z + 1 
				inteIndex = inteIndex + 1
				if inteIndex > 0:  return          # We work with first only.



	##########################################################################
	def readPORVarray(self,fd): 
		print "Reading PORV array"
		self.m_PORVarray= []           #to keep a list of the PORV records.
		nTDP = -1 
		nPOV = -1 
		for n in self.records:
			fPOV = find(n[0],'PORV')
			if fPOV == 0: nPOV = n[1]
			fTDP = find(n[0],'TDEPTH')
			if fTDP == 0: nTDP = n[1]
			if nTDP > 0 and nPOV > 0 and nTDP == nPOV: 
				if self.verbose ==1 : print "No need for pore volume."
				return 
		for n in self.records:
			if (find(n[0],'PORV') == 0):
				#porv = numpy.array([],'f')
				fd.seek(n[3]+28,0)            # Seek to the data
				br = fd.read(n[1]*4)
				porv = numpy.fromstring(br,'f')
				if sys.byteorder == 'little': porv = porv.byteswapped()  # if on Intel
				self.m_PORVarray.append(porv)

	##########################################################################
	def readOneBlock(self,bindex,how='REAL'):
		"""
		Reads one complete block.
		"""
		if self.lastIndexFetched == bindex : return self.lastArrayFetched 
		n = self.records[bindex]
		if self._fd == None: self._fd = open(self.filename,'rb')
		fd = self._fd
		fd.seek(n[3]+28,0)           # Seek to start of record.
		if how in ['CHAR','MESS']:
			retarray = fd.read(n[1]*8)
		else:
			br = fd.read(n[1]*4)
			retarray = numpy.fromstring(br,self.arrayTypeCodes[how])
			if sys.byteorder == 'little' and self.dataOrder == 'big': retarray = retarray.byteswapped()  
		self.lastIndexFetched = bindex; 
		self.lastArrayFetched = retarray
		return retarray

	def not_working_readOneBlock(self,bindex,how='REAL'):
		"""
		Does read the complete block! 
		"""
		if self.lastIndexFetched == bindex :
			return self.lastArrayFetched 
		n = self.records[bindex]
		fr = uECLRecord()
		fd = open(self.filename,'rb')
		fd.seek(n[3],0) # 
		r = fr.readECLrecord(fd)  # item contains data.
		if how == 'DOUB':retarray = numpy.array('d')
		if how == 'REAL':retarray = numpy.array('f')
		if how == 'INTE':retarray = numpy.array('i')
		if how == 'LOGI':retarray = numpy.array('i')
		if r > 0: 
			if how == 'CHAR' or how == 'MESS': 
				retarray = fr.item
			else:
				retarray.fromstring(fr.item)
				if sys.byteorder == 'little' and self.dataOrder == 'big':
					retarray = retarray.byteswapped()  # if on Intel and data from non-Intel
			self.lastIndexFetched = bindex; 
			self.lastArrayFetched = retarray
		fd.close()
		return retarray

#######################################################################
# This class handles ECL INIT files.
#######################################################################
class basicRFTfile(basicECLfile):
	def __init__(self):
		basicECLfile.__init__(self) # ,ofile)    # Get the record names and sizes
		self.dataType = 'RFT'  # This must be set before opening the file 

#######################################################################
# This class handles ECL INIT files.
#######################################################################
class basicINITfile(basicECLfile):
	def __init__(self):
		basicECLfile.__init__(self) # ,ofile)    # Get the record names and sizes
		self.dataType = 'INIT'  # This must be set before opening the file 

	def getWellNames(self):
		return "None"

#######################################################################
# This class handles ECL INIT files.
#######################################################################
class basicUNRSTfile(basicECLfile):
	def __init__(self):
		basicECLfile.__init__(self) 
		self.dataType = 'UNRST'    # This must be set before opening the file 
		self.data = None	               # Used as temp variable.
		self.tree = None	 			   # for displaying..
		self.dr = None	

	def getWellNames(self):
		"""
			Loads the names of the wells from the first INTEHEAD 
			object.

			TODO: Allow for different INTEHEAD objects
		"""
		names = [] 
		inteObj = self.m_INTEHEADarray[0]
		z = 0
		while z < inteObj.nwell:
			well = inteObj.m_wells[z]
			names.append(well.name)
			z = z + 1
		names.sort()
		return names

	def getWellIJKList(self,name):
		"""
		Returns a list with IJK values 
		"""
		inteObj = self.m_INTEHEADarray[0]
		for well in inteObj.m_wells:
			if name.find(well.name) > -1: return well.points
		return []

	def getWellIJK(self,name):
		"""
		Returns a text string with IJK values per line for named well.
		"""
		ijkValues = ''
		inteObj = self.m_INTEHEADarray[0]
		z = 0
		while z < inteObj.nwell:
			well = inteObj.m_wells[z]
			if name == well.name:
				for pt in well.points:
					ijkValues = ijkValues + join(map(str,pt),' ') + '\n'	
				return ijkValues
			z = z + 1
		return 'None'

##############################################################################
#  Not derived from basicECLfile data holder class
#
#  It can be created from scratc.
##############################################################################
class basicGRIDfile:
	def __init__(self):
		self.dataType = 'GRID'
		self.acount = 0
		self.nx = 0
		self.ny = 0
		self.nz = 0 
		self.nCells = 0 			# Temp variables 
		self.active = None
		self.boxOrigion= [0,0,0]
		self.gridUnit = "Meter"
		self.records = None
		self.dr = None	
		self.m_numGrids = 0 
		self.m_lgrActive = []
		self.m_lgrDepths = []
		self.m_lgrXarray = []
		self.m_lgrYarray = []
		self.m_lgrDeltaXarray = []
		self.m_lgrDeltaYarray = []
		self.m_dimensions = []
		self.m_lgrDimensions = []  
		self.pickledGridName = None
		self.filename = None
		self.nactiv = 0

	
	def getDepthArray(self,i=0):
		"""
		The index should be the LGR number, not the record number
		"""
		if i >= len(self.m_lgrDepths) or i < 0: i = 0
		return self.m_lgrDepths[i] 

	#
	# This should really be saved with the pickle...
	#
	def getDepthRange(self,i=0):
		"""
		The index should be the LGR number, not the record number
		"""
	
		#print "Returning depth..", i
		if i >= len(self.m_lgrDepths) or i < 0: i =0
		a = self.m_lgrDepths[i] 
		
		vmin = a[0]
		vmax = a[0]
		klen = len(a)
		k = 1
		while k < klen:
			v = a[k]
			if v < vmin: vmin = v
			if v > vmax: vmax = v
			k = k + 1
		return vmin,vmax


	def setDepthArray(self,d,i=0):
		if len(self.m_lgrDepths) < 1: 
			self.m_lgrDepths.append(d)
			#print "Setting new depth..."
		else: 
			self.m_lgrDepths[i]  = d
			#print "Setting depth ..."

	def setDeltaYarray(self,d,i=0):
		if len(self.m_lgrDeltaYarray) < 1: 
			self.m_lgrDeltaYarray.append(d)
		else: 
			self.m_lgrDeltaYarray[i]  = d

	def setDeltaXarray(self,d,i=0):
		if len(self.m_lgrDeltaXarray) < 1: 
			self.m_lgrDeltaXarray.append(d)
		else: 
			self.m_lgrDeltaXarray[i]  = d

	def setYarray(self,d,i=0):
		if len(self.m_lgrYarray) < 1: 
			self.m_lgrYarray.append(d)
		else: 
			self.m_lgrYarray[i]  = d

	def setXarray(self,d,i=0):
		if len(self.m_lgrXarray) < 1: 
			self.m_lgrXarray.append(d)
		else: 
			self.m_lgrXarray[i]  = d

		
	def getDeltaYarray(self,i):
		if i >= len(self.m_lgrDeltaYarray) or i < 0:  i = 0
  		return self.m_lgrDeltaYarray[i] 

	def getXarray(self,i=0):
		if i > len(self.m_lgrXarray) or i < 0: i =0
		a =  self.m_lgrXarray[i] 
		#print "I have ", len(self.m_lgrXarray), " LGRS"
		# for k in range(10): print "X[",k,"]=",a[k]
		return self.m_lgrXarray[i] 

	def getYarray(self,i=0):
		if i >= len(self.m_lgrYarray) or i < 0: i =0
		a =  self.m_lgrYarray[i] 
		# for k in range(10): print "Y[",k,"]=",a[k]
		return self.m_lgrYarray[i] 

	def getDeltaXarray(self,i=0):
		if i >= len(self.m_lgrDeltaXarray) or i < 0:  i =0
		return self.m_lgrDeltaYarray[i] 

	def getActiveArray(self,i=0):
		if i >= len(self.m_lgrActive) or i < 0: i = 0
		return self.m_lgrActive[i] 

	######################################################################
	# Overrides the basic ECL file.
	# This must be mirrored in the dumpArrays function.
	######################################################################
	def openFile(self,ofile):
		if self.filename == ofile:	return
		self.filename = ofile
		(filepath,filename) = os.path.split(ofile)
		(shortname,bigextension) = os.path.splitext(filename)
		env = os.getenv('RS3DTEMP')
		if env == None:  
			if os.name == 'nt': 
				env = '.'
			else:
				env = os.getenv('HOME')
		tempDirName = env + os.sep
		self.pickledGridName = tempDirName + shortname + bigextension + ".pickled"
		if os.path.exists(self.pickledGridName) == False:
			self.readNewGrid()	
		else: 
			self.loadArrays(self.pickledGridName)
		return



	def flushGridCache(self):
		if self.pickledGridName <> None:
			try:
				os.unlink(self.pickledGridName)
				self.pickledGridName = None
			except:
				pass

	######################################################################
	# Don't use directly. Use the openFile function instead.
	######################################################################
	# This must be mirrored in the dumpArrays function.
	# self.filename and self.pickledGridName must be set ere this call.
	######################################################################
	def readNewGrid(self,dump=1):
		self.xxtime = time() # DETERMINE IF YOU ARE IN GRID OR EGRID
		ff =  upper(self.filename[-5:])
		if ff == 'EGRID':
			if self.verbose ==1 : print "Reading EGRID"
			r = self.readEGrid(self.filename)	# Read GRID file from disk
			if r==0: 
				print "Unable to open the file ...", self.filename
				return
			self.constructDXDY()	# Construct DX_ROW and DY_ROW
		else:
			r = self.readGrid(self.filename)	# Read GRID file from disk
			if r==0: 
				print "Unable to open the file ...", self.filename
				return
			self.constructDXDY()	# Construct DX_ROW and DY_ROW
			#
			# Here you have to create the dX and dY arrays.
			#
		if self.verbose ==1 : print "Time taken to read from disk...", time() - self.xxtime
		if dump==1: self.dumpArrays(self.pickledGridName)		# Save for fast recovery later.

	######################################################################
	# This must be mirrored in the dumpArrays function.
	######################################################################
	def loadArrays(self,name):
		xxtime = time()
		fd = open(name,'rb')
		self.m_lgrActive = []  
		self.m_lgrDepths = []
		self.m_lgrXarray = []
		self.m_lgrYarray = []
		self.m_lgrDeltaX = []
		self.m_lgrDeltaY = []
		self.m_dimensions = []
		PU = pickle.Unpickler(fd)
		header = PU.load()
		for i in range(header[0]): 
			x = PU.load(); d=numpy.array('i'); d.fromstring(x)
			self.m_lgrActive.append(d);
		for i in range(header[1]): 
			x = PU.load(); d=numpy.array('f'); d.fromstring(x)
			self.m_lgrDepths.append(d)
		for i in range(header[2]): 
			x = PU.load(); d=numpy.array('f'); d.fromstring(x)
			self.m_lgrXarray.append(d)
		for i in range(header[3]): 
			x = PU.load(); d=numpy.array('f'); d.fromstring(x)
			self.m_lgrDeltaX.append(d)
		for i in range(header[4]): 
			x = PU.load(); d=numpy.array('f'); d.fromstring(x)
			self.m_lgrYarray.append(d)
		for i in range(header[5]): 
			x = PU.load(); d=numpy.array('f'); d.fromstring(x)
			self.m_lgrDeltaY.append(d)
		for i in range(header[6]): 
			self.m_dimensions.append(PU.load())
		fd.close()
		print "Time taken to read grid file from disk...", time() - xxtime


	######################################################################
	# This must be mirrored in the loadArrays function.
	######################################################################
	def dumpArrays(self,filename):
		xxtime = time()
		fd = open(filename,'wb')
		header = [len(self.m_lgrActive), len( self.m_lgrDepths), len( self.m_lgrXarray),\
		len( self.m_lgrDeltaX), len( self.m_lgrYarray), len( self.m_lgrDeltaY),len(self.m_dimensions)]
		PU  = pickle.Pickler(fd)
		PU.dump(header)
		for xess in self.m_lgrActive:  PU.dump(xess.tostring())
		for xess in self.m_lgrDepths:  PU.dump(xess.tostring())
		for xess in self.m_lgrXarray:  PU.dump(xess.tostring())
		for xess in self.m_lgrDeltaX: PU.dump(xess.tostring())
		for xess in self.m_lgrYarray:  PU.dump(xess.tostring())
		for xess in self.m_lgrDeltaY: PU.dump(xess.tostring())
		for xess in self.m_dimensions: PU.dump(xess)
		if self.verbose ==1 : print "Time taken to write to disk...", time() - xxtime
		fd.close()

	######################################################################
	# Part 1: Make the DX_ROW and DY_ROW ... required for display later
	######################################################################
	def makeDifferences(self,ldata):
		xlen = len(ldata)
		i = 1
		x = 0
		da = numpy.array('f')
		#xarray.append(0)           # For LGR, this will be non-zero
		while i < xlen:
			dx = ldata[i] - ldata[i-1]	
			da.append(dx)
			i = i + 1
		#print "Making .....", len(da), da[:5]
		return da	

	######################################################################
	# Part 2:   
	######################################################################
	def constructDXDY(self):
		self.m_lgrDeltaX = [] 		# Init and release
		self.m_lgrDeltaY = []
		#print "Constructing DX DY" 
		for xess in self.m_lgrXarray:
			if self.verbose ==1 : print xess[:5]
			v = self.makeDifferences(xess)
			self.m_lgrDeltaX.append(v)
		for xess in self.m_lgrYarray:
			v = self.makeDifferences(xess)
			self.m_lgrDeltaY.append(v)


	def readEGrid(self,filename,intelligent=0):
		try:
			#print "Opening [", filename,"]"
			dr = open(filename,'rb')
		except:
			print "Unable to open file...", filename
			return 0	
		self.incomingRecord = uECLRecord()						# New empty record.
		self.intelligent = intelligent 		    # Later...
		self.cornerCount = 0					# Count corners.
		self.acount = 0						    # and active cells.
		retCount = self.incomingRecord.readECLrecord(dr) 	# Read into record.
		while (retCount> 0):				    # Till EOF 
			self.parseEGridRecord(self.incomingRecord)			    # Parse into array.
			retCount = self.incomingRecord.readECLrecord(dr)# Next
		dr.close()						    # Close the file.
		return 1	

	def parseEGridRecord(self,record):
		keyword = strip(record.eclHead.keyword)
		if (keyword == "GRIDHEAD"):
			fmtstr = fmt_dynamicStr + str(record.eclHead.iItemCount) + 'l'
			fmtitems = unpack(fmtstr,record.eclData.item)       # Get dimensions
			self.nx = fmtitems[1]
			self.ny = fmtitems[2]
			self.nz = fmtitems[3]
			self.nCells = self.nx * self.ny * self.nz
			self.nxy    = self.nx * self.ny					    # Layer size
			self.m_dimensions.append((self.nx,self.ny,self.nz,self.nxy,self.nCells)) # Save it.
			return 
		if (keyword == "COORD"):
			self.xarray = numpy.array(self.xarray,'f')
			self.yarray = numpy.array(self.yarray,'f')
			#self.m_lgrXarray.append(self.xarray)
			#self.m_lgrYarray.append(self.yarray)
			self.cornerCount = 0
			k = 0
			for i in xrange(self.nx+1):
				v = unpack(fmt_singleFloatStr,record.item[k:k+4])
				k = k + 24
				self.xarray.append(v[0])
			for i in xrange(self.ny+1):
				k = 4 + (self.nx+1) * i * 24   # This is goofy... it's nx+1, not nx
				v = unpack(fmt_singleFloatStr,record.item[k:k+4])
				self.yarray.append(v[0])
			print "____________ COORD ______ ", len(self.xarray), self.xarray[:5], self.nx+1
			return 
		if (keyword == "ZCORN"):
			self.depths = numpy.array(self.depths,'f')
			#self.m_lgrDepths.append(self.depths)
			k = 0
			count = 0
			ll = len(record.item)
			nxy = self.nx * self.ny * 8
			nx4 = self.nx * 4
			for z in xrange(0,self.nz):
				for y in xrange(0,self.ny):
					for x in xrange(0,self.nx):
						k = ((x*2) + (y * nx4) +  (z * nxy)) * 4
						v = unpack(fmt_singleFloatStr,record.item[k:k+4])
						self.depths.append(v[0])
						count = count + 1
			#print "I have found ... ", count, "depth cells;"

		if (keyword == "ACTNUM"):
			self.active = array(self.active,'i')			# Create filter arrays 
			#self.m_lgrActive.append(self.active)
			sz =  self.nx * self.ny * self.nz
			self.active.fromstring(record.item)
			if sys.byteorder == 'little': self.active = self.active.byteswapped()  # if on Intel
			count = 0
			for j in range(len(self.active)):
				if self.active[j] <> 0: 
					count = count + 1
			if self.verbose ==1 : print "I have found ... ", count, "active cells;"
				

	######################################################################
	# Reads and ECL grid files' items  into arrays. Slow. 
	######################################################################
	def readGrid(self,filename,intelligent=0):
		try:
			#print "Opening [", filename,"]"
			dr = open(filename,'rb')
		except:
			print "Unable to open file...", filename
			return 0	
		
		self.incomingRecord = uECLRecord()						# New empty record.
		self.intelligent = intelligent 		    # Later...
		self.cornerCount = 0					# Count corners.
		self.acount = 0						    # and active cells.
		self.fullgrid = 0					    # if active==nCells
		retCount = self.incomingRecord.readECLrecord(dr) 	# Read into record.
		while (retCount> 0):				    # Till EOF 
			self.parseRecord(self.incomingRecord)			    # Parse into array.
			retCount = self.incomingRecord.readECLrecord(dr)# Next
		dr.close()						    # Close the file.
		print "Count of active cells = ", self.acount, len(self.active), len(self.xarray), len(self.yarray)
		return 1
	
	######################################################################
	# Workhorse routine for all GRID records
	# Rules 
	# 1. If NACTIV == NX * NY * NZ then all cells active; ignore coords.
	######################################################################
	def parseRecord(self,record):
		self.verbose = 0
		keyword = strip(record.eclHead.keyword)
		if (keyword == "CORNERS"):
			(x,y,z)= unpack(fmt_tripleFloatStr,record.eclData.item[0:12])   #
			if self.cornerCount < self.nx: 
				self.xarray.append(x)
				if self.cornerCount < 1: self.yarray.append(y)
				self.depths.append(z)
				self.cornerCount = self.cornerCount + 1
				return
			if ((self.cornerCount % self.nx) == 0) and len(self.yarray) < (self.ny+1): 
				self.yarray.append(y)
				self.depths.append(z)
			else:
				#corners= unpack(fmt_singleFloatStr,record.eclData.item[8:12])
				#self.depths.append(corners[0])
				#self.depths.fromstring(record.eclData.item[8:12])
				self.depths.append(z)
			self.cornerCount = self.cornerCount + 1
			if self.cornerCount % 1000 == 0: 
					print "Read", self.cornerCount, "/", self.nCells, "tm", time() - self.xxtime, "\r"
			return
		if (keyword == "COORDS"):
			if self.fullgrid == 1: return   		# Ignore COORDS if full grid.
			ln = len(record.eclData.item)		    # Only active type of cells.
			active = 1								# All active unless suggested
			if ln == 20 or ln == 28: 				# Only these.
				active = unpack(fmt_singleLongStr,record.eclData.item[16:20])
			if active: 
				self.acount = self.acount+1
				self.active.append(1)
			else:
				self.active.append(0)
			return
		if keyword == 'DIMENS':
			if self.verbose ==1 : print "DIMENS"
			fmtstr = fmt_dynamicStr + str(record.eclHead.iItemCount) + 'l'
			fmtitems = unpack(fmtstr,record.eclData.item)       # Get dimensions
			self.nx = fmtitems[0]
			self.ny = fmtitems[1]
			self.nz = fmtitems[2]
			self.nCells = self.nx * self.ny * self.nz  			# And the size
			self.nxy    = self.nx * self.ny					    # Layer size
			if self.verbose ==1 : print "---> %d %d %d ... nxy = %d " % (self.nx,self.ny,self.nz,self.nxy)
			self.m_dimensions.append((self.nx,self.ny,self.nz,self.nxy,self.nCells)) # Save it.
			self.xarray.append(0.0)
			self.yarray.append(0.0)
			self.active = numpy.array(self.active,'i')			# Create filter arrays 
			self.depths = numpy.array(self.depths,'f')
			self.xarray = numpy.array(self.xarray,'f')
			self.yarray = numpy.array(self.xarray,'f')
			#self.m_lgrActive.append(self.active)
			#self.m_lgrDepths.append(self.depths)
			#self.m_lgrXarray.append(self.xarray)
			#self.m_lgrYarray.append(self.yarray)
			self.cornerCount = 0
			if self.nactiv == self.nCells: 	
				self.fullgrid = 1
				self.incomingRecord.skipList = ['COORDS']
				self.acount   = self.nCells
				if self.verbose ==1 : print "Full grid, skipping", self.nCells, "COORDS"
				# Create your active array or do you need it?
				#k = 0 while k < self.nCells: self.active.append(1)
			else:
				self.incomingRecord.skipList = []
				self.fullgrid = 0
			return
		if keyword == 'GRIDUNIT': 
			self.gridUnit = record.eclData.item
		# if keyword == "LGR": print "LGR found" 
			return
		if keyword == "LGRILG": 
			fmtstr = fmt_dynamicStr + str(record.eclHead.iItemCount) + 'l'
			fmtitems = unpack(fmtstr,record.eclData.item)
			# print "LGRILG", fmtitems
			self.m_lgrDimensions.append(fmtitems)
			return
		if keyword == 'BOXORIG': # This is a global parameter.
			fmtstr = fmt_dynamicStr + str(record.eclHead.iItemCount) + 'l'
			fmtitems = unpack(fmtstr,record.eclData.item)
			self.boxOrigin=fmtitems[0:3]
			return
		#print keyword

class basicFileHeader:
	def __init__(self,nx,ny,nz):
		self._nx = nx
		self._ny = ny
		self._nz = nz

	def setDataSize(self,a):
		self._nx = a[0]
		self._ny = a[1]
		self._nz = a[2]

	def getDataSize(self):
		return (self._nx, self._ny , self._nz )

	def setAttrNames(self,names): 
		self._attrNames = names

	def getAttrNames(self):
		return self._attrNames

class basicECLobject:
	"""
	###################################################################################
	# Class that encapsulates UNRST, GRID and INIT files in one convenient place.
	# I avoid reading the GRID or EGRID file unless absolutely necessary. 
	###################################################################################
	"""
	def __init__(self,progressNotify=None):
		self.filename =None
		self.progressNotify = progressNotify   # Progress meter function 
		self.initHandler    = None             # Only in the case of UNRST file
		self.inputHandler   = basicECLfile()   # Create the object for the input.
		self.gridHandler    = basicGRIDfile()  # Create a placeholder.
		self.header         = basicFileHeader(0,0,0)

		self.lgrIndex = 0  		# Index into INTEHEAD array
		self.lastIndex = -1 		# Index into Data record array
		self.lastArray = None		# improve the cache.
		self.lastMinV = 0.0
		self.lastMaxV = 1.0
		self.maxX = 0
		self.maxY = 0
		self.maxZ = 0
		self.dX = None
		self.dY = None
		self.dZ = None
		self.minSummedX = 0
		self.maxSummedX = 0
		self.minSummedY = 0
		self.maxSummedY = 0
		self.bypassDimensions = 0 

		#
		# The following is a list of names that cannot be plotted 
		#
		self.errors   = []
		self.usingPowers = 1
		self.requestedLGRindex  = -1   # July 5, 2004       - Set to 0 to N-1 LGRS

	def getCalcDX(self,maxX,lgr_index=0):
		self.dX = self.gridHandler.getXarray(lgr_index)
		ndx = int(maxX-1)
		print "Index = ", maxX, len(self.dX), type(self.dX) , self.dX[-1]
		self.minSummedX = self.dX[0]                # Get the limit 
		self.maxSummedX = self.dX[ndx]
		return self.minSummedX, self.maxSummedY, self.dX

	def getCalcDY(self,maxY,lgr_index=0):
		self.dY = self.gridHandler.getYarray(lgr_index)
		ndx = int(maxY-1)
		print "Type of maxY", type(maxY), maxY, ndx
		self.minSummedY = self.dY[0]                # 
		self.maxSummedY = self.dY[ndx]     
		return self.minSummedY, self.maxSummedY, self.dY

	def readHeader(self,whence=None):
		pass

 	#####################################################################################
	def openFile(self,ofile,usePowers=1):
		if self.filename == ofile: return		# Don't open the file twice
		self.filename = ofile					# Must have INIT or UNRST extension
		(filepath,filename) = os.path.split(ofile) # Get the base directory
		(shortname,fullextension) = os.path.splitext(filename)  # The base file 
		if not fullextension in ['.INIT','.UNRST','.init','.unrst']: 
			self.errors = "Unable to open file ... check extension for %s " % ( self.filename )
			return 


		self.gridName = None 
		#####################################################################################
		# First check if you have an EGRID file  
		#####################################################################################
		if fullextension in ['.INIT','.UNRST'] : 
			self.gridName =  self.filename.replace(fullextension,'.EGRID')
		if fullextension in ['.init','.unrst'] : 
			self.gridName =  self.filename.replace(fullextension,'.egrid')
		if self.gridName <> None:
			try:
				r = os.stat(self.gridName)
			except:
				self.gridName = None
				# This is where you will see if a grid occurs.
				#self.errors = "Unable to make out the egrid file ... check extension for %s " % ( ofile )

		if self.gridName == None:
			if fullextension in ['.INIT','.UNRST'] : 
				self.gridName =  self.filename.replace(fullextension,'.GRID')
			if fullextension in ['.init','.unrst'] : 
				self.gridName =  self.filename.replace(fullextension,'.grid')
		
		if self.gridName == None:
			print  "Unable to make out the  grid file ... check extension for %s " % ( ofile )
		try:
			r = os.stat(self.gridName)
		except:
			#self.errors = "Unable to make out the  grid file ... check extension for %s " % ( ofile )
			print  "Unable to make out the  grid file ... check extension for %s " % ( ofile )
			#return None

		#####################################################################
		# Don't  
		#####################################################################
		#self.usingPowers = usePowers
		#f self.usingPowers == 0:
		#self.gridHandler.openFile(self.gridName)# Now open the file or read from cache.

		if fullextension in ['.INIT','.init']  : 
			self.inputHandler = basicINITfile()
			self.inputHandler.openFile(self.filename)    # open it and set the type.
			self.m_PORVarray = self.inputHandler.m_PORVarray    # KEEP A COPY
			##############################################################	
			found = 0;
			found1 = 0 
			found2 = 0 
			found3 = 0 
			for r in self.inputHandler.getAttrNames():
				n,dt,sz=split(r)
				if n == 'TDEPTH': found1 = 1
				if n == 'DX': found2 = 1
				if n == 'DY': found3 = 1
				if n == 'PORV': print "Name = [%s],[%s],[%s]\n" % (n,dt,sz)
				if found1 and found2 and found3:
					found = 1 
					break

			##############################################################	
			if self.bypassDimensions == 0: 
				if found == 1:
				# Read DX, DY, DZ, TDEPTH and create the DX,X,DY,Y arrays.
					self.createGridArrays(fromwhence=None)
					self.usingPowers = 1
				else: 
					self.usingPowers = 0
					print "INIT: NOT USING POWERS...", self.gridName 
					self.gridHandler.openFile(self.gridName)# Now open the file or read from cache.
			return
		if fullextension in ['.UNRST','.unrst']: 
			self.inputHandler = basicUNRSTfile()
			self.inputHandler.openFile(self.filename)    # open it and set the type.
			self.initHandlerName =  self.filename.replace('.UNRST','.INIT')
			self.initHandlerName =  self.initHandlerName.replace('.unrst','.init')
			self.initHandler = basicINITfile()
			self.initHandler.openFile(self.initHandlerName)    # open it and set the type.
			self.m_PORVarray = self.initHandler.m_PORVarray    # KEEP A COPY
			found = 0
			foundDX = 0;
			foundDY = 0;
			foundTDEPTH = 0;
			for r in self.initHandler.getAttrNames():
				n,dt,sz=split(r)
				#print "UNRST Name = [%s]\n" % n
				if n == 'TDEPTH': foundTDEPTH = 1
				if n == 'DX': foundDX = 1
				if n == 'DY': foundDY = 1
				if n == 'PORV': print "Name = [%s],[%s],[%s]\n" % (n,dt,sz)
				if foundDX and foundDY and foundTDEPTH: 
					found = 1
					break;
			if self.bypassDimensions == 0: 
				if found == 1:
					############################################################################
					# Read DX, DY, TDEPTH from the INIT file and create the DX,X,DY,Y arrays.
					self.createGridArrays(fromwhence=self.initHandler)
					self.usingPowers = 1
					#print "USING POWERS...", 
				else: 
					self.usingPowers = 0
					#print "NOT USING POWERS...", self.gridName 
					self.gridHandler.openFile(self.gridName)# Now open the file or read from cache.
			return
		self.errors = "Unable to open file ... check extension for %s " % ( self.filename )

	################################################################################
	def createGridArrays(self,fromwhence=None):
		"""
		If you are opening an INIT file then fromwhence = self otherwise 
		the fromwhence is set to the input handler for the INIT file for 
		the UNRST file currently open. 
		"""
		self.dZ = self.readAttributeDataByName(attrName='DZ',handler=fromwhence)  # This will be full array 
		self.maxX,self.maxY,self.maxZ = self.getDimensions()
		print "Dimensions: ", self.maxX,self.maxY,self.maxZ
		self.header.setDataSize(self.getDimensions())
		self.header.setAttrNames(self.getAttrNames())

		a = self.readAttributeDataByName(attrName='DX',handler=fromwhence)        # This will be full array 
		deltaX  = a[0:self.maxX]
		self.gridHandler.setDeltaXarray(deltaX)
		"""
		dX = array('f')
		dX.append(0)
		for i in range(self.maxX): v = dX[i] + deltaX[i]; dX.append(v)
		self.gridHandler.setXarray(dX)
		self.dX = dX
		"""
		dX = range(self.maxX+1)
		for i in range(0,self.maxX): dX[i+1] = dX[i] + deltaX[i]
		self.dX = dX
		self.gridHandler.setXarray(numpy.array(dX,'f'))
		print "---> Assigning ", len(dX), " items to dX", self.maxX, dX[1],dX[2]
		
		a = self.readAttributeDataByName(attrName='DY',handler=fromwhence)     # This will be full array 
		deltaY = []
		n = self.maxX * self.maxY
		for i in range(0,n,self.maxX): deltaY.append(a[i])
		self.gridHandler.setDeltaYarray(deltaY)
		dY = []
		dY.append(0)
		for i in range(self.maxY):
                    v = deltaY[i] + dY[i];
                    dY.append(v)
		self.dY = numpy.array(dY,'f')
		self.gridHandler.setYarray(self.dY)
		print "---> Assigning ", len(dY), " items to dY", self.maxY, self.dY[:5], deltaY[:5]
		depths = self.readAttributeDataByName(attrName='TDEPTH',handler=fromwhence)    
		ddepths = self.readAttributeDataByName(attrName='TDEPTH',handler=fromwhence)    
		ddepths.sort()
		self.maxZvalue = ddepths[-1]
		self.minZvalue = ddepths[0]
		ddepths = None
		self.gridHandler.setDepthArray(depths)
		
	################################################################################
	def getWellNames(self):
		return self.inputHandler.getWellNames()

	################################################################################
	def getHeaderStrings(self,verbose=0): 
		return self.inputHandler.getAttrNames()   #  Full list

	################################################################################
	def getAttrNames(self):
		"""
		Removes bogus names such SEQNUM, INTEHEAD, LOGIHEAD, IWEL, etc.
		Actually, we should only keep those for which there is an LGR or a master INTEHEAD!!!
		"""
		retnames = []
		for rec in self.inputHandler.records:
			if not rec[0] in self.inputHandler.bogusNames:
				#
				# Only allow valid sizes. 
				#
				sz = rec[1]
				if sz in self.inputHandler.m_INTEHEADsizes:
					xstr = rec[0] + " " +  rec[4] + " [" + str(rec[1]) + "]" 
					retnames.append(xstr)
		#retnames.sort()
		retnames.sort(lambda x,y:(cmp(split(x)[-1],split(y)[-1]) or cmp(x,y)))
		names = ['DEPTH'] + retnames
		return names

	def getTimeSteps(self):
		return self.getNarrowInformation(4)

	def getAttrSizes(self):
		return self.getNarrowInformation(5)


	def getNarrowInformation(self,whence=4):
		"""
			whence == 0 for attr name 
			whence == 1 for size
			whence == 4 for time 
			whence == 5 for attr + size 
		"""
		retnames = []
		for rec in self.inputHandler.records:
			if not rec[0] in self.inputHandler.bogusNames:
				#
				# Only allow valid sizes. 
				#
				sz = rec[1]
				if sz in self.inputHandler.m_INTEHEADsizes:
					if whence == 5: 
						xstr = rec[0] + " = [" + str(rec[1]) + "]" 
					else: 
						xstr = rec[whence] 
					if not xstr in retnames:
						retnames.append(xstr)
		retnames.sort()
		return retnames
		
	def getWellStrings(self):
		return "getWellStrings is not implemented in ECLOBJECT"


	def readAttributeDataByName(self,attrName,pfunction=None,handler=None):
		"""
		BasicECLobject
		Input:
			attrName = attributeName <space> date <space> LGRname
			if LGRname == 'Full', use the first available.
			
		"""
		if attrName == 'DEPTH' and  self.usingPowers == 0:
			return self.gridHandler.m_lgrDepths[0] 
		if handler == None: handler = self.inputHandler

		items = split(attrName)
		bindex = -1                             #  
		attr = []
		if len(items) == 1: 
			for rec in handler.records:
				bindex = bindex +1
				if rec[0] == items[0]:
					stime = time()
					dblock = handler.readOneBlock(bindex,rec[2]); 
					attr = self.decompressData(0, bindex, dblock)
					print "1894 Time to read ", attrName, time() - stime
					break
			return attr


		###################################### Okay, 
		# attr + time + lgr requested. 
		bindex = -1                             #  
		seqcount = -1 
		lgrcount = -1

		#######################################################################
		# July 18, 2005 Kamran. Use master if bogus sequence number.
		#######################################################################
		seqWanted = -1
		print "Seq number = ", len(handler.m_SEQNUMS) , items[1]
		if len(handler.m_SEQNUMS) > 0: 
			try:
				seqWanted = handler.m_SEQNUMS.index(items[1])     #
			except:
				seqWanted = 1

		lgrname = items[2] 
		if lgrname == 'Full': 
			lgrWanted = -1
		else:
			lgrWanted = handler.m_LGRNAMES.index(lgrname)
		#print "XXXY items ", items		
		#print "XXXX seqnums ", handler.m_SEQNUMS
		#print "XXXX seqWanted = " , seqWanted, items[1]
		#print "XXXX lgrWanted = " , lgrWanted, lgrname
		how = 'REAL'
		for rec in handler.records:
			if find(rec[0],'SEQNUM') == 0: 
				lgrcount = -1
				seqcount = seqcount+1      # Check if you have crossed 
			if len(rec[0]) == 3:		   # Look only for "LGR"
				if find(rec[0],'LGR') == 0: 
					lgrcount = lgrcount + 1
			bindex = bindex +1             #
			if lgrcount == lgrWanted and seqcount == seqWanted  and items[0] == rec[0]:
				how = rec[2]
				break;
		if bindex < 0: return []
		#print "bindex = ", bindex, " length = ", len(handler.records), how
		stime = time()
		dblock = handler.readOneBlock(bindex,how); 
		etime = time()
		print "Time to read ",len(dblock), " ", etime - stime 
		attr = self.decompressData(lgrWanted+1, bindex, dblock)
		print "Time to decompress ",len(dblock), " ", time() - etime 
		self.lgrIndex = lgrWanted + 1
		#print "Returning ", len(attr) , " items for ", attrName, "lgrIndex = ", self.lgrIndex
		return attr


	def getRequestedLGR(self): return	self.requestedLGRindex 
	def setRequestedLGR(self,n=-1):
		self.requestedLGRindex = n 
		if n < 0 or n >= len(self.inputHandler.m_LGRNAMES): 
			self.requestedLGRindex = -1 
	
	def getLGRnames(self): return self.inputHandler.m_LGRNAMES
	def getLGRindex(self): return self.lgrIndex
	def getWellIJK(self,name): return self.inputHandler.getWellIJK(name)

	def getDimensions(self,inteIndex=0):
		inteObj = self.inputHandler.m_INTEHEADarray[inteIndex]
		return inteObj.nx,inteObj.ny,inteObj.nz
		
	################################################################################
	# The indexToUse is used in the activeArray 
	################################################################################
	def decompressData(self,indexToUse,attrIndex,datablock):   
		print "decompressData ", len(datablock), " bytes with  lgrIndex=", indexToUse
		if self.lastIndex == attrIndex:
			print "---> Returning last decompressed ", attrIndex
			self.minV  = self.lastMinV 
			self.maxV  = self.lastMaxV
			return self.lastArray

		#print "Len of active arrays", len(self.gridHandler.m_lgrActive)
		#for i in range(len(self.gridHandler.m_lgrActive)):
			#print "-->[%d] = %d" % (i,len(self.gridHandler.m_lgrActive[i]))
		decomp = 1
		if len(self.m_PORVarray) < 1:       decomp = 0
		if len(self.m_PORVarray) > 0:       
			self.activeArray = self.m_PORVarray[indexToUse]
			if len(self.activeArray) == len(datablock): 
				decomp = 0

		if decomp == 0:
			#self.minV = min(datablock)
			#self.maxV = max(datablock)
			self.minV = datablock.min()
			self.maxV = datablock.min()
			self.lastMaxV  = self.maxV
			self.lastMinV  = self.minV
			self.Range = self.maxV - self.minV
			self.lastIndex = attrIndex
			self.lastArray = datablock
			print "No decompression, only range check:",self.minV,self.maxV
			return datablock

		inteObj = self.inputHandler.m_INTEHEADarray[indexToUse]
		dims =  inteObj.nz,inteObj.ny,inteObj.nx
		size =  inteObj.nx * inteObj.ny * inteObj.nz
		print "Get ", len(self.activeArray), " active cells. " , len(datablock), dims, size

		v = 0
		i = 0
		k = 0
		attribute = numpy.zeros(size)
		xcount = 0
		for a in self.activeArray: 				  # Map grid into active array
			if (a <> 0):
				try:
					attribute[k]=datablock[i]
					i = i + 1
				except:
					pass
			k = k + 1
		self.minV = min(attribute)
		self.maxV = max(attribute)
		print "Return..", len(attribute) , "cells from", i, " active cells. " , self.minV, self.maxV
		self.lastMinV  = self.minV  # Keep copy ...
		self.lastMaxV  = self.maxV
		self.lastIndex = attrIndex
		self.lastArray = attribute
		attribute = numpy.reshape(attribute,dims)
		print "Active cells ", self.activeArray[:4], attribute.shape 
		return attribute

		## Modification - m001 
		jlen = 0 
		if self.gridHandler <> None and self.usingPowers == 0:
			self.activeCells = self.gridHandler.getActiveArray(indexToUse)
			jlen= len(self.activeCells) 
			if len(self.activeCells) == len(datablock) or jlen == 0:
				decomp = 0
			else:
				decomp = 1
		## EndModification - m001 
		print "Check..",jlen," vs "," Data..", len(datablock) , " data cells. " 

		v = 0
		i = 0
		attribute = numpy.zeros(size)
		xcount = 0
		for a in self.activeCells: 				  # Map grid into active array
			if (a == 0): 
				v=0
			else:
				try:
					v=datablock[i]
					i = i + 1
					xcount = xcount + 1
				except:
					pass
			attribute.append(v)
		self.minV = min(attribute)
		self.maxV = max(attribute)
		print "Return..", len(attribute) , "cells from", xcount, " active cells. " , self.minV, self.maxV
		print "Active cells ", self.activeCells[:4]
		self.lastMinV  = self.minV  # Keep copy ...
		self.lastMaxV  = self.maxV
		self.lastIndex = attrIndex
		self.lastArray = attribute
		return attribute

###################################################################################
# Test routine for the cache.
###################################################################################

if __name__ == '__xmain__':
	if (len(sys.argv) < 1): print "specify a file name"; exit(0);
	xx = basicINITfile(sys.argv[1])

# The command line must specify a complete file name

	###################################################################
	# Get the extension: 
	# if INIT or init  : then simply create the index file.
	# if UNRST or unrst: then simply create the index file.
	# if GRID or grid  : then read the INIT file first to get nactiv.

def doMe(daname):
	(filename,extension) =  os.path.splitext(daname)
	if extension in [".INIT", ".init"]: 
		xx = basicINITfile()
		xx.openFile(daname)
	
		print xx.getAttrNames()
		x = 'DX'
		for r in xx.getAttrNames():
			n,dt,sz=split(r)
			if n == x:
				print "I have found DX", r

		sys.exit(0)
	if extension in [".UNRST", ".unrst"]: 
		xx = basicUNRSTfile()
		xx.openFile(daname)
		sys.exit(0)

	######################################################################
	# Okay, it is a GRID file..
	######################################################################
	if extension in [".GRID", ".grid"]: 
		if extension == ".GRID":
			initfilename = filename + ".INIT"
		else: 
			initfilename = filename + ".init"
		xx = basicINITfile()             # Now get the nactiv  
		xx.openFile(initfilename)             # Now get the nactiv  
		pint = xx.m_INTEHEADarray[0]                 # get list of INTEHEAD 
		xg = basicGRIDfile()
		xg.nactiv = pint.nactiv
		print "Active cells = ", pint.nactiv 
		xg.openFile(daname)

	######################################################################
	# Business .. The extract is done as part of a POWERS run. We can 
	# tack ourselves to it.
	######################################################################


def main():
	doMe('hm01b.grid')

if __name__ == '__gmain__':
	if (len(sys.argv) < 1): print "specify a grid file name"; exit(0);
	doMe(sys.argv[1])

if __name__ == '__main__':
	if (len(sys.argv) < 1): print "specify a file name"; exit(0);
	dr = open(sys.argv[1],'rb')
	fr = uECLRecord()
	retCount = fr.readECLrecord(dr)
	while (retCount> 0):
		print fr.eclHead.keyword,fr.eclHead.iItemCount,fr.eclHead.iType, dr.tell()
		#retCount = fr.listECLrecord(dr)
		#fr.dumpAsText()
		retCount = fr.readECLrecord(dr)
	dr.close()
	sys.exit(0)
