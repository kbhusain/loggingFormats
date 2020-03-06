#!/peasd/fesg/users/husainkb/lnx/usr/local/bin/python 

##
# Copy a LAS and instert a parameters (~P) block if necessary for GEOLOG 6.7
#
from pLASutils import *

if __name__ == '__main__':
	setName = 'RAWDATA'
	print sys.argv
	if len(sys.argv) < 2: 
		print "Cannot process", sys.argv
		sys.exit(0)
	if len(sys.argv) > 3: 
		setName = sys.argv[3]
	led = lasReader()
	led.setSetName(setName)    # Must be set before you open the file
	led.openFile(sys.argv[1])  # Now read and replace set name 
	led.writeLASout(sys.argv[2])

