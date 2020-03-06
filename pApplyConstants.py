#!/peasd/fesg/users/husainkb/lnx/usr/local/bin/python
import sys, os

from nrtp_jobfile import *


if __name__ == '__main__':
	if len(sys.argv) < 2: 
		print "Usage: prog geologDump SpecIn SpecOut"
		sys.exit(0) 

	geologIn = sys.argv[1] 
	specIn   = sys.argv[2]
	specOut  = sys.argv[3]   

	print "lne IN" , len(sys.argv)
	print "GEOLOG IN" , sys.argv[1] 
	print "SPEC IN" , sys.argv[2] 
	print "SPEC oUT" , sys.argv[3] 
	

	gf      = geologJobFile();  gf.parseJobFile(geologIn)   	
	spec_in = geologSpecFile(); spec_in.parseSpecFile(specIn)   	

	skeys = spec_in.constants.keys()
	for sc in skeys:
		value = gf.constants.get(sc,None)
		if value == None : continue
		if value == 'N/A': value = ''
		spec_in.constants[sc] = value
	
	spec_in.writeFile(specOut) 
