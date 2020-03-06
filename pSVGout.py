
import os, sys 


svgPreamble = """<?xml version="1.0" standalone="no"?>
<svg  xmlns="http://www.w3.org/2000/svg"      xmlns:xlink="http://www.w3.org/1999/xlink"
viewBox="-40 -100 1000 590" preserveAspectRatio="none" version="1.1">

"""

svgTerminator = """</svg>"""

svgStyles = """
<style type="text/css"> 
<![CDATA[
	.FontTextAnchorMiddle{text-anchor:middle;}
	.FontTextAnchorLeft{text-anchor:left;}
	.FontTextAnchorRight{text-anchor:right;}
	%s 

  ]]>
</style> 
"""

PIXELS_PER_INCH = 90.0; 


class SVGout: 
	def __init__(self):
		#-------------------------------------------------------------------------------------
		# Elements of style:
		#-------------------------------------------------------------------------------------
		self.stroke = "black"
		self.fill = "white"
		self.strokewidth = 1
		self.fontsize = 11 
		self.style = "stroke:%s;stroke-width:%f;fill:%s" % (self.stroke,self.strokewidth,self.fill)
		self.units = ""
		self.width = "100%"
		self.height = "100%"
		#-------------------------------------------------------------------------------------
		# Outputs 
		#-------------------------------------------------------------------------------------
		self.preamble = svgPreamble ; # % (self.width, self.height)
		self.xmlLines = [] 
		self.terminator = svgTerminator
		self.minY = 1000000.0;
		self.maxY = -100000.0; 
		self.minX = 1000000.0;
		self.maxX = -100000.0; 
		self.Yscale = 1
	
	def reverseYscale(self) : self.Yscale = -1; 
	def setStrokeWidth(self,num=1): self.strokewidth = float(num)

	##########################################################################
	# Always sets in pixels, 
	def setLimits(self,wd,ht,units="px"):
		if units == 'in': 
			self.width = str(wd  * PIXELS_PER_INCH) 
			self.height = str(ht * PIXELS_PER_INCH) 
		else:
			self.width = str(wd) + self.units
			self.height = str(ht) + self.units
	
	def getXMLout(self): 
		# outstr = [svgPreamble % (self.width, self.height),] 
		outstr = [svgPreamble , ] 
		for xl in self.xmlLines: 		outstr.append(xl)
		outstr.append(self.terminator)
		return "\n".join(outstr)
	
	def addSVG(self,rawSVG) : self.xmlLines.append(rawSVG) 

	def addHeaderImage(self,filename,x1,y1,wd,ht,units=""):
		self.xmlLines.append('<image xlink:href="%s"  x="%f%s" y="%f%s" width="%f%s" height="%f%s" />' \
			% ( filename,x1,units,y1,units,wd,units,ht,units) ) 
		
	##
	# Adds a line to output buffer. 
	# 	
	def addLine(self,x1,y1,x2,y2,units="",stroke="black",strokewidth=1,id="None", strokedasharray=None):
		if units == "in": 
			x1 = x1 * PIXELS_PER_INCH 
			y1 = y1 * PIXELS_PER_INCH 
			x2 = x2 * PIXELS_PER_INCH 
			y2 = y2 * PIXELS_PER_INCH 
		y1 = y1 * self.Yscale
		y2 = y2 * self.Yscale
		style = "stroke:%s;stroke-width:%f%s" % (stroke,strokewidth,units)
		if strokedasharray: 
			style += ';stroke-dasharray:%s' % strokedasharray
		self.xmlLines.append('<line x1="%f" y1="%f" x2="%f" y2="%f" style="%s" />\n' \
			% ( x1,y1,x2,y2,style) ) 

	##
	# Polygon or Polyline - The first parameter specifies how to fill or not to fill - that is the question
	# Units are sent in as inches by defaults - We convert to pixels on the fly for the svg element
	# 
	def addPolyLine(self,polygon=0,units="in",stroke="black",strokewidth=0.1,strokedasharray=None,fill="none",points=[]):
		if (len(points) < 2):return  	
		if units == "in": strokewidth *= PIXELS_PER_INCH 
		pathList = 'stroke="%s" stroke-width="%f" fill="%s"' % (stroke,strokewidth,fill)  
		if strokedasharray: 
			pathList += ' stroke-dasharray="%s"' % strokedasharray
		self.xmlLines.append('<path  ' + pathList) 
		normalized = [ PIXELS_PER_INCH * d for d in points ] 
		self.xmlLines.append('d="M%f,%f ' % (normalized[0], normalized[1] * self.Yscale))
		ln = len(normalized) 
		for x in range(2,ln,2):
			self.xmlLines.append('L%f,%f ' % (normalized[x], normalized[x+1] * self.Yscale))
		if polygon == 1: 
			#self.xmlLines.append('L%f,%f ' % (normalized[-2], normalized[-1] * self.Yscale))
			self.xmlLines.append('Z"/>') 
		else:  
			self.xmlLines.append('"/>') 
	
	##
	# Adds a line to output buffer. 
	# 	
	def addRectangle(self,id,x,y,w,h,units="",fill_style="none",fill_color="none",strokewidth=0,stroke_color='black'):
		if strokewidth == 0 and fill == "none": return 
		# Accummulate the style. 
		style = "" 
		if strokewidth > 0: style += "stroke-width:%f" % (strokewidth * PIXELS_PER_INCH) 
		if fill_style != 'none': 
			style += ";fill:%s" % fill_color
		else:
			style += ";fill:none"
		style += ";stroke:%s" % stroke_color
		if units == "in": 
			x = x * PIXELS_PER_INCH 
			y = y * PIXELS_PER_INCH 
			w = w * PIXELS_PER_INCH 
			h = h * PIXELS_PER_INCH 
		y = y * self.Yscale
		self.xmlLines.append('<rect id="%s" x="%f" y="%f" width="%f" height="%f" style="%s"/>'  % ( id,x,y,w,h,style) ) 
	
	##
	# defaults.parameters must have set the following items:
	# ['color_line']
	# ['char_height']
	# ['rotate'] to the value of the matrix in c5
	# 
	def addTextTag(self,x,y, outstr,defaults,anchor="start",color='black',units="",fontsize=10,verticalAlignment=0,matrix=None):
		if units == "in": 
			x = x * PIXELS_PER_INCH 
			y = y * PIXELS_PER_INCH 
		y = y * self.Yscale
		dy=0
		rotationStr = "" 
		fontsize = int( PIXELS_PER_INCH  * defaults.parameters['char_height'])   # Pixels per inch 
		if matrix: 	
			if verticalAlignment==1: dy=fontsize * -1
			if verticalAlignment==5: dy=fontsize 
			rotationStr = ' transform="matrix(%f,%f,%f,%f,%f,%f)" ' % (matrix[1], matrix[0], matrix[3], matrix[2], x + dy, y  ) 
			self.xmlLines.append('<text style="text-anchor:%s" font-size="%f" %s ><tspan fill="%s">%s</tspan></text>' % (anchor,fontsize,rotationStr,color,outstr))
		else:	
			#if verticalAlignment==1: dy=fontsize
			#if verticalAlignment==5: dy=fontsize*-0.2                # Usually for the title
			if verticalAlignment==1: dy=fontsize
			if verticalAlignment==5: dy=fontsize * -1
			self.xmlLines.append('<text style="text-anchor:%s" font-size="%f"  ><tspan x="%f" y="%f"  dy="%f" fill="%s">%s</tspan></text>' \
				% (anchor,fontsize,x,y,dy,color,outstr))

		


