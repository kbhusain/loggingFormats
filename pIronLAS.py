## 
#---------------------------------------------------------------------------
# A very simple LAS parser for reading in LAS 2.0 files. 
# Kamran Husain 
# TODO:
#   1. Read wrapped lines - NOT supported in LAS 3.0 
#   2. Add a LAS writer program - Not Needed 
#   3. Add code to read LAS 3.0 sections - Done.
#   4. Accomodate formatting - Not Needed 
#   5. Allow for delimiters other than 'space' for columns - Done
#---------------------------------------------------------------------------
import sys, math, re
from time import ctime, time

class p_lasObject:
	def __init__(self,cname,units='',dvalue=0.0,desc=''):
		self.cname = cname;
		self.units = units;
		self.dvalue = dvalue
		self.desc = desc
		self.data = [] 
		#if 1:			print cname, units, dvalue, desc
	def appendData(self,v): self.data.append(v)
	
class p_lasWriter:
	def __init__(self,filename=None):
		self.filename = filename
	
	##
	# NOT WORKING SINCE NO REQUIREMENT
	# csvName is the name of the csv file. 
	# The first row must contain row definitions.
	# There must be a DEPTH column.
	def csvToLAS(self,csvName,lasName,sep=','):
		fd = open(lasName,'w');
		#fd.write(preamble); 
		#Get the column headers from first row.
		fd.close()
	
	
#-----------------------------------------------------------------------
# LAS reader class in python.
#-----------------------------------------------------------------------
class p_lasReader: 
	def __init__(self,filename=''):
		self.re_parm  = re.compile('([A-Z][A-Z ]+\.[\w%/]*) (.*):(.*)')
		self.filename = filename; 
		self.nullValue = -999.25
		self.wrap  = False;
		self.delim = None; # default space, could be TAB or COMMA
		self.records = {}
		if len(self.filename) > 0: self.readFile(filename)

	def readFile(self,filename):
		self.filename = filename;
		xlines = open(filename,'r').readlines()
		self.records = {}    # Initialize the records
		token = '' 
		for ln in xlines:
			if ln[0] == '~':
				token = ln.split()[0]
				self.records[token] = []
			self.records[token].append(ln)
			
		# I will only parse the sections I need. 
		self.version  = self.parseSection('~VERSION',None)
		self.setVersionDefaults()
		self.wellInfo = self.parseSection('~WELL',None)
		self.curveNames = []
		self.curves   = self.parseSection('~CURVE',self.curveNames)
		self.core = self.parseSection('~CORE',None)
		self.inclinometry  = self.parseSection('~INCLINOMETRY',None)
		self.drilling  = self.parseSection('~DRILLING',None)
		self.tops   = self.parseSection('~TOPS',None)
		self.testParms = self.parseSection('~TEST',None)
		self.parameters  = self.parseSection('~PARAMETER',None)
		self.information = self.parseSection('~OTHER',None)
		self.createDataArrays()
		
	def setVersionDefaults(self):
		#if self.version.has_key('WRAP'): self.wrap = self.version['WRAP'].dvalue.strip();
		if self.version.has_key('DLM'): self = self.version['DLM'].dvalue.strip()
	
	def createDataArrays(self):
		# Create a dictionary of names
		# First determine if the WRAP is ON. 
		for ln in self.records['~ASCII']:
			if ln[0] in ['~', '#']: continue
			if self.delim != None:
				items = map(float,ln.split())
			else:
				items = map(float,ln.split(self.delim))
			i = 0
			for nm in self.curveNames:
				self.curves[nm].appendData(items[i])
				i + 1
	
	def parseSection(self,sectionName,order=None):
		obj = {}
		if not self.records.has_key(sectionName): return []
		for ln in self.records[sectionName]:
			if ln[0] in ['~', '#']: continue
			ma  = self.re_parm.match(ln)
			if ma:
				cname,units = ma.group(1).split('.')
				obj[cname] = p_lasObject(cname,units,ma.group(2 ),ma.group(3))
				if order != None: order.append(cname)
		return obj

	def getColumnNames(self): return self.curves.keys(); 
	def getNullValue(self): return self.nullValue;
	def getVectorData(self,csName=None):
		if csName==None: return [];
		return self.curves[csName].data
	
	def getXYData(self,filename=None,xName=None,yName=None):
		if xName==None or yName == None:
			return [],[];
		print self.curveNames
		return self.curves[xName].data, self.curves[yName].data


	
if __name__ == '__main__':
	led = p_lasReader(sys.argv[1])
	skeys = led.wellInfo.keys()
	skeys.sort()
	for k in skeys:
		print k, led.wellInfo[k].dvalue, led.wellInfo[k].desc
	#print led.getXYData(sys.argv[1],'DEPT','QWZTR')
