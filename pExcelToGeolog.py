##
# Converts formation pressure data into csv format
import os, sys

from xlrd import  open_workbook 
from pGeologSpecFile import *
from nrtp_jobfile import geologSet 

lnames = [ "DEPTH" , "FORM_PRES","MOBILITY"]
lunits = ["FT","PSIA","MD/CP"]

EXCEL_COLUMNS_SCHLUMBERGER = [ 2, 9 , 10 ]
EXCEL_COLUMNS_HALLIBURTON    = [ 3, 8 , 9 ]
EXCEL_COLUMNS_HALLIBURTON_2  = [ 3, 13 , 18 ]
EXCEL_COLUMNS_BAKER        = [ 4, 8 , 9 ]


##
#
def getPyrolysisDataAsCSV(filename, serviceCompany): 
	columns = EXCEL_COLUMNS_BAKER
	if serviceCompany == 'Baker': 		columns = EXCEL_COLUMNS_BAKER
	if serviceCompany == 'Halliburton':	columns = EXCEL_COLUMNS_HALLIBURTON
	if serviceCompany == 'Schlumberger': 	columns = EXCEL_COLUMNS_SCHLUMBERGER
	wb = open_workbook(filename)
	sheet = wb.sheet_by_index(0) 
	outstr = []
	outstr.append(",".join(lnames))
	outstr.append(",".join(lunits))
	for row in range(14, sheet.nrows):
		values = [] 
		for col in  columns : 
			v = sheet.cell(row,col).value
			if len(str(v)) < 1:        v = sheet.cell(row,6).value
			if v < 1.0 and col == 8 :  v = sheet.cell(row,6).value
			values.append(str(v))
		ostr = " ".join(values)
		if len(ostr) > 2: outstr.append(ostr)
	return "\n".join(outstr)

##
#
def getDataBlockFromExcel(filename, serviceCompany) :
	wb = open_workbook(filename)
	outarray = []
	columns = EXCEL_COLUMNS_BAKER
	print serviceCompany	
	backwards = True 
	if serviceCompany == 'Baker': 		columns = EXCEL_COLUMNS_BAKER; startRow = 14 
	if serviceCompany == 'Halliburton': 	columns = EXCEL_COLUMNS_HALLIBURTON; startRow = 14 
	if serviceCompany == 'Schlumberger': 	columns = EXCEL_COLUMNS_SCHLUMBERGER; startRow = 9 
	for sheet in wb.sheets(): 
	#	sheet = wb.sheet_by_index(0) 
		f = sheet.name.find('Client') 
		g = sheet.name.find('Drilling') 
		h = sheet.name.find('TESTS') 
		if f < 0 and g < 0 and h < 0: continue
		if h > -1: columns = EXCEL_COLUMNS_HALLIBURTON_2; startRow = 10 ; backwards = False 
		print "f = ", f, " g = ", g,  "h = " , h, columns, sheet.nrows
		for row in range(startRow, sheet.nrows):
			if 1:	
				values = [] 
				rfp = 0
				for col in columns : 
					v = sheet.cell(row,col).value
					#print "v=", v, row, col
					if backwards:
						if len(str(v)) < 1:        v = sheet.cell(row,col - 1 ).value
						if v < 1.0 and rfp == 1 :  v = sheet.cell(row,col - 1 ).value
						if v < 1.0 and rfp == 1 :  v = sheet.cell(row,col - 2 ).value
					else: 
						if len(str(v)) < 1:        continue 
					if v < 1.0: continue
					values.append(v)
					rfp += 1
				if len(values) != len(columns): continue
				if values[0] == '': continue
				print "Values = ", values, len(columns) 
				outarray.append(values) 
			if 1:
				pass

	if len(outarray) > 1: 
		print "This data from ", filename, " is to ", outarray[-1][0]

		#------------------- DUPLICATE LAST ROW----------------- PER PMN request
		lastRow = outarray[-1][:]
		outarray.append(lastRow) 

	return outarray


if __name__ == '__main__': 
	wellname = sys.argv[1]          # well name 
	filename = sys.argv[2]          # excel file 
	serviceCompany = 'Baker' 
	if len(sys.argv) > 2: serviceCompany = sys.argv[3] 
	data = getDataBlockFromExcel(filename,serviceCompany) 
	#print csvout 
	header = "*HEADER  GEOLOG LOG Geolog Dump File"
	gset = geologSet() 
	cols = [[ 'DEPTH', 'FT', 'DOUBLE' ], 
		[ 'FORM_PRES', 'FT', 'DOUBLE' ], 
		[ 'MOBILITY', 'FT', 'DOUBLE' ]
		]
	gset.setName('FORM_PRES')  
	gset.setData( cols, data ) 
	dump = gset.getGeologDump(hole=wellname) 
	########################################################################
	print header,
	print dump
	

