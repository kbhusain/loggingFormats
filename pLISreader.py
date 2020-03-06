#
# ---------------------------------------------------------------
# Converts DLIS files to LIS files
#
# ---------------------------------------------------------------
import os, sys, struct

from ctypes import *

##
# States 

LIS_STATE_0  = 0 
LIS_REEL_H   = 1 
LIS_TAPE_H   = 2
LIS_FILE_H   = 3
LIS_REEL_T   = 4
LIS_TAPE_T   = 5
LIS_FILE_T   = 6


recordTypes = [ "FILE_HEADER", "ORIGIN", "AXIS", "CHANNEL", "FRAME", "CALIBRATION", "COMMENT", 
	"UPDATE", "NO-FORMAT", "LONG-NAME", "ATTRIBUTE", "SPEC", "DICT" ]


class lis_LRHS(Structure):
	_fields_ = [
		('LogicalRecordSegmentLength', c_ushort),
		('LogicalRecordSegmentAttributes', c_ubyte),
		('LogicalRecordType', c_ubyte),
		]
	
	def unpack(self,data):
		self.LogicalRecordSegmentLength , \
		self.LogicalRecordSegmentAttributes, self.LogicalRecordType = struct.unpack('>Hbb',data)
		


##
# File Header Trailer
class lis_FHLR(Structure):
	_fields_ = [ 
		('LogicalHeader', c_ushort), 
		('FileName', c_char * 10), 
		('Unused', c_ushort), 
		('ServiceSubLevelName', c_char * 6), 
		('VersionNumber', c_char * 8), 
		('GenerationDate', c_char * 8), 
		('Blank1', c_char), 
		('MaxRecordLength', c_char * 5), 
		('Blank2', c_ushort), 
		('FileType', c_char * 2), 
		('Blank3', c_ushort), 
		('OptionalName', c_char * 10), 
		]

	def unpack(self, data):
		fmtstr = '>H10sH6s8s8sc5sh2sh10s'
		self.LogicalHeader, self.FileName,	self.Unused,\
		self.ServiceSubLevelName,	self.VersionNumber,\
		self.GenerationDate,	self.Blank1,\
		self.MaxRecordLength,	self.Blank2,\
		self.FileType,  		self.Blank3,\
		self.OptionalName =  struct.unpack(fmtstr,data[:58])
		
	def dump(self):
		print self.LogicalHeader, self.FileName
		print self.ServiceSubLevelName,	self.VersionNumber
		print self.GenerationDate
		print self.MaxRecordLength
		print self.FileType
		

##
# Tape Header Trailer
#
# Reel header Trailer
class lis_RHLR(Structure):
	_fields_ = [ 
		('LogicalHeader', c_ushort), # H
		('ServiceName', c_char * 6), # 6c
		('Blank1', c_char * 6),    # 3H
		('GenerationDate', c_char * 8), # 8c 
		('Blank2', c_ushort),           #  H
		('OriginData', c_char * 4),     # 4c 
		('Blank3', c_ushort),           #  H
		('TapeName', c_char * 8),       # 8c 
		('Blank4', c_ushort),           #  H
		('TapeNumber', c_char * 2),     # 2c
		('Blank5', c_ushort),           #  H
		('PreviousTape', c_char * 8),   # 8c
		('Blank6', c_ushort),           #  H
		('OptionalName', c_char * 74),  # 74c
		]

	def unpack(self, data):
		fmtstr = '>H6s6s8sH4sH8sH2sH8sH74s'
		[self.LogicalHeader,		self.ServiceName, 		self.Blank1, \
		self.GenerationDate,		self.Blank2,		self.OriginData,\
		self.Blank3,		self.TapeName,		self.Blank4,\
		self.TapeNumber,		self.Blank5,		self.PreviousTape,\
		self.Blank6,	self.OptionalName] = struct.unpack(fmtstr,data[:128])
		
	def dump(self):
		print self.LogicalHeader
		print self.ServiceName 	
		print self.GenerationDate
		print self.OriginData
		print self.TapeName
		print self.TapeNumber
		print self.PreviousTape
		print self.OptionalName
#
#
class lis_LRS:
	##
	# 
	def __init__(self):
		self.state = 0
		self.fd = None
		self.filename = None;
		self.records = []
		self.recordTypes = recordTypes[:]
		self.tapeHeader = None;
		self.reelHeader = None
		for n in range(len(recordTypes),128):
			self.recordTypes.append("UNKNOWN %d" % n);
			
	def readReelHeader(self,data): 
		self.reelHeader = lis_RHLR()
		self.reelHeader.unpack(data)
		self.reelHeader.dump()

	def readTapeHeader(self,data): 
		self.tapeHeader = lis_RHLR()
		self.tapeHeader.unpack(data)
		self.tapeHeader.dump()

	def readFileHeader(self,data): 
		self.fileHeader = lis_FHLR()
		self.fileHeader.unpack(data)
		self.fileHeader.dump()
		


	def processRecord(self,typeOfRecord,data):
		if self.state == LIS_STATE_0 and typeOfRecord == 0x84:
			self.state = LIS_REEL_H
			self.readReelHeader(data)
		if self.state == LIS_REEL_H and typeOfRecord == 0x82:
			self.state = LIS_TAPE_H
			self.readTapeHeader(data)
		if self.state == LIS_TAPE_H and typeOfRecord == 0x80:
			self.state = LIS_FILE_H
			self.readFileHeader(data)
	##
	#
	def readRecord(self, sz):
		fx = "%d %d " % (self.fd.tell(), sz)
		db = self.fd.read(4)               # Read block header 
		if len(db) <= 0: return -1         # Bail on EOF
		x = lis_LRHS(); x.unpack(db)       # Unpack it. 
		data = self.fd.read(x.LogicalRecordSegmentLength - 4)   # Read rest of values
		if len(data) <=0: return -1        # Bail on EOF
		#print "Read in %d " % (len(data))  # Let me know how much I read. 
		if (x.LogicalRecordSegmentAttributes & 1): 	print "Padding byte included"
		#print "RECORD TYPE: %s" % self.recordTypes[x.LogicalRecordType]
		typeOfSet = struct.unpack(">B",data[0])[0]
		if typeOfSet > 0: 
			print fx, "%d %X %d %x" % (x.LogicalRecordSegmentLength , \
				x.LogicalRecordSegmentAttributes, x.LogicalRecordType, typeOfSet)
			self.processRecord(typeOfSet,data)
		return x.LogicalRecordSegmentLength
		
		
	
	##
	# 
	def readFile(self,filename):
		self.filename = filename;
		self.fd = open(filename,'rb')
		sz = os.stat(filename).st_size
		self.state = LIS_STATE_0
		while 1:
			r = self.readRecord(sz)
			if r < 0: break;
		print os.stat(filename).st_size
		


if __name__ == '__main__':
	xx = lis_LRS();
	xx.readFile(sys.argv[1])
	

