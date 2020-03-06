#
#
#

import os, sys, shutil
from pLASutils import p_lasReader, p_simpleLASwriter, p_lasObject, p_lasWriter

##
#
class pCombineLAS:
	def __init__(self): 
		self.option=None
		pass 	

	def combineFiles(self,las1,las2,lasMerged,wellname=None,setName='QUICKLOOK'):
		self.debug = 1 
		self.nm_las1 = las1
		self.nm_las2 = las2
		self.nm_lasMerged = lasMerged

		# Take care of null conditions first
		if las1 == None and las2 == None: return 

		if las1 == None and las2: 
			shutil.copyfile(las2,lasMerged) 
			return
		if las2 == None and las1: 
			shutil.copyfile(las1,lasMerged) 
			return
		# file name is valid but and empty one! Where's xor?
		if os.path.exists(las1) and  not os.path.exists(las2): 
			shutil.copyfile(las1,lasMerged) 
			return
		if not os.path.exists(las1) and os.path.exists(las2): 
			shutil.copyfile(las2,lasMerged) 
			return
			
		# Okay, both exist
		self.f_las1 = p_lasReader(las1) 
		self.f_las2 = p_lasReader(las2) 
		self.f_merged = p_simpleLASwriter() 

	
		d1min,d1max = self.f_las1.getDepthRange() 
		d2min,d2max = self.f_las2.getDepthRange() 
		totalRange = min(d1min,d2min), max(d1max,d2max) 
		allCurves  = { } 

		if self.debug > 0: 
			print "Range of depth for las1 = ", d1min, d1max
			print "Range of depth for las2 = ", d2min, d2max
			print "Total Range of depth  = ", totalRange

			print "Curves las1 = ", self.f_las1.curveNames, len(self.f_las1.curveNames) 
			print "Curves las2 = ", self.f_las2.curveNames, len(self.f_las2.curveNames) 

		allCurveObjects = { } 
		allCurveNames   = [ ] 
		allUnitNames    = [ ] 
		for nm in self.f_las1.curveNames: 
			if not nm in allCurveNames: 
				obj = self.f_las1.curves[nm] 
				allCurveObjects[nm] = p_lasObject(obj.cname,obj.units,obj.dvalue,obj.desc) 
				allCurveNames.append(nm) 
				allUnitNames.append(obj.units) 
				
		for nm in self.f_las2.curveNames: 
			if not nm in allCurveNames: 
				obj = self.f_las2.curves[nm] 
				allCurveObjects[nm] = p_lasObject(obj.cname,obj.units,obj.dvalue,obj.desc) 
				allCurveNames.append(nm) 
				allUnitNames.append(obj.units) 

		if self.debug > 0: 
			print "All curves = ", allCurveNames, len(allCurveNames) , len(allCurveObjects.keys()) 
			print "All curves = ", allUnitNames, len(allUnitNames) 
		# Now create the new depth array at the required intervals 
		lasout = p_lasWriter() 


		#----------------------------------------------------------------------------------
		# Create depth array for the full range at 0.5 foot intervals 
		#----------------------------------------------------------------------------------
		dataBlock = { } 
		depth = totalRange[0] 
		dpName = allCurveNames[0] 
		justCurveNames = allCurveNames[1:]                        # Get curve names to work with. 
		while depth < totalRange[1]:
			dataBlock[depth] = {} 
			block = dataBlock[depth]
			block[dpName] = depth                             # Set Depth to first column
			for nm in justCurveNames: block[nm] = -999.25
			depth += 0.5 
		#----------------------------------------------------------------------------------

		#----------------------------------------------------------------------------------
		# Create data array for the full range at all depth intervals
		#----------------------------------------------------------------------------------
		depth = totalRange[0] 
		while depth < totalRange[1]:
			#print "Processing Depth", depth , totalRange
			block = dataBlock[depth]
			for nm in justCurveNames: 
				if nm in self.f_las1.curveNames: 
				 	block[nm] = self.f_las1.getCurveDataValue(nm,depth) 
				if nm in self.f_las2.curveNames: 
				 	block[nm] = self.f_las2.getCurveDataValue(nm,depth) 
				if block[nm] > 100 and nm == 'MT_PHIAX' : print nm, depth, block[nm] 
			depth += 0.5 
		#----------------------------------------------------------------------------------
		skeys = dataBlock.keys()
		skeys.sort() 

		lasout.setSetName(setName) 
		for nm in justCurveNames: 
				if nm in self.f_las1.curveNames: 
					lasout.setCurveObject(nm,self.f_las1.curves[nm]) 
				if nm in self.f_las2.curveNames: 
					lasout.setCurveObject(nm,self.f_las2.curves[nm]) 
				 	

		lasout.setSetName(setName) 
		lasout.setCurveNames(allCurveNames) 
		lasout.setUnitNames(allUnitNames) 
		# Now add some data lines 
		#print "------------Adding lines"
		for dp in skeys:
			#print "------------Adding line at", dp
			block = dataBlock[dp] 
			dblock = [ block[nm] for nm in allCurveNames ] 
			dblock = map(str,dblock) 
			lasout.addCurveDataLine(" ".join(dblock))
		#print "------------Done with lines"
		#------------------------------------------------------------------------------------

		for section in [ '~W', '~WELL', '~P', '~PARAMETER' ] : 
			lasout.addRecordsForSection(section,self.f_las1.records) 
			lasout.addRecordsForSection(section,self.f_las2.records) 

		lasout.adjustWellSection() 
		if self.option == '-filled': self.fillInColumns(lasout) 
		lasout.writeFile(lasMerged,wellname,wrap="YES") 

	def fillInColumns(self,lasout):
		v0 = lasout.datalines[0].split()    # Get initial Vector
		newdataLines = [" ".join(v0),] 
		for vn in lasout.datalines[1:]:
			v1 = vn.split() 	
			i = 0 
			nv = [] 
			for vr in v1:
				if vr != '-999.25': v0[i] = vr
				nv.append(v0[i])
				i += 1
			newdataLines.append(" ".join(nv))
		lasout.datalines = newdataLines 
		


if __name__ == '__main__':
	print sys.argv
	if len(sys.argv) > 3: 
		combined = pCombineLAS() 
		combined.combineFiles(sys.argv[1],sys.argv[2],sys.argv[3]) 
	if len(sys.argv) > 4: 
		combined = pCombineLAS() 
		if sys.argv[4] == '-filled': 
			wellname= None
			combined.option = sys.argv[4]	
		else:
			wellname= sys.argv[4] 
			combined.option = None	
		combined.combineFiles(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4]) 
