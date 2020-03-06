# ---------------------------------------------------------------
#
#
# ---------------------------------------------------------------
import os, sys, struct

#
class dlis_LRS:
	##
	# 
	def __init__(self):
		self.log_recordLength = 0 
		self.log_attributes = 0
		self.log_recordType = 0
		self.log_recordData = None
	##
	# 
	def getData(self,fd):
		item = fd.read(4)  # Read 4 bytes 
		self.log_recordLength, self.log_attributes, self.log_recordType = struct.unpack('>HBB',item)
		print self.log_recordLength, self.log_attributes, self.log_recordType ;

class pDLIS:
	##
	# 
	def __init__(self):
		self.filename = ''
		self.debug = 1
		self.data  = None
	
	##
	# 
	def processHeader(self,fd):
		bytes = fd.read(80)
		self.sequenceNumber = bytes[:4]
		self.versionNumber = bytes[4:9]
		self.unitStructure = bytes[9:16]
		self.maxRecordLen  = bytes[15:20]
		self.identifier = bytes[20:]
		#---------------------------- 
		if self.debug > 0: 
			print self.sequenceNumber 
			print self.versionNumber 
			print self.unitStructure 
			print self.maxRecordLen  
			print self.identifier
	##
	#
	def readData(self,fd):
		self.data = ''
		df = fd.tell()
		b = fd.read(2)
		while b: 
			jump = int(struct.unpack('>H',b)[0])
			print fd.tell(), jump
			d = fd.read(jump-2); # Read past physical block.
			if (d <= 0) : break;
			self.data += d   # append ; 
			b = fd.read(2)
		print "Len of data ", len(self.data)
		
	##
	# 
	def readFHLR(self):
		if self.data == None: return
		# Skip FF01
		print "Service name = ", self.data[4:10]
		
		b = self.data[2:4]
		self.fhlr = {}
		self.len_fhlr = int(struct.unpack('>H',self.data[2:4])[0]) # 
		self.fhlr['SEQUENCE_NUMBER'] = self.data[49:59]
		self.fhlr['ID'] = self.data[61:125]
		print "Logical Record Segment Length=", self.len_fhlr, self.fhlr
		
		self.beg_fhlr = 2 
	
	def readOrigin(self):
		self.beg_origin = self.beg_fhlr + self.len_fhlr + 2 
		b = self.data[self.beg_origin:self.beg_origin+3]
		self.len_origin, self.attr_origin = map(int,struct.unpack('>Hb',b)) #
		print self.len_origin, "Origin Record Segment Length=", self.beg_origin
		rec_origin = self.data[self.beg_origin:self.beg_origin+self.len_origin]
		p = 3
		while p < self.len_origin:
		#for k in range(21):
			ct = struct.unpack('>b',rec_origin[p])[0]     # Length of object. 
			name  = rec_origin[p+1:p+ct+1]                # name of object. 
			m = struct.unpack('>b',rec_origin[p+ct+1])[0]
			if m < 0x30: 
				print "Up", p, ct, name,  len(name); 
				ct += 1; 
			else:
				print "As", p, ct, name,  len(name); 
			value = struct.unpack('>c',(rec_origin[p+ct+1:p+ct+2]))[0]
			p  += ct + 2
		return self.beg_origin+self.len_origin
			
		
		
	##
	#
	def openFile(self,filename):
		self.filename = filename
		fd = open(filename,'rb')
		self.processHeader(fd)
		self.readData(fd);  
		self.readFHLR();
		#self.readOrigin(); 
		#fd.close()
		
	def dumpData(self,fout):
		fd = open(fout,'wb')
		fd.write(self.data)
		fd.close()
		
if __name__ == '__main__':
	
	xx = pDLIS();
	xx.openFile(sys.argv[1])
	xx.dumpData("out2.dat")
	
	