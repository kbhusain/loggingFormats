import os,sys

if __name__ == '__main__':
	filenames = sys.argv[1:]
	n = 0
	for file in filenames: 
		try: 
			if n: 	
				xlines = open(file,'r').readlines()[1:]
			else: 
				xlines = open(file,'r').readlines()
			for xl in xlines: 
				items = xl.strip().split(',')
				if len(items) != 13: continue	
				print xl, 
			n +=1
			print
		except: 
			pass


