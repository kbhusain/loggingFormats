#!/bin/csh -f
# DESCRIPTION
# Export log data from EXPLWLS data sets for all wells in a project in DLIS format
# using logdb  translation.
#	| tp_name_translate name_translation = logdb.names to_geolog = false \

# Get list of wells
global env 

set $env(PG_SITE)      /peasd/geolog/prod/site 

set wellName $env(PG_WELL) 
set setName  $env(SET_NAME)
set outfile  $env(OUTDIR)/${wellName}_${setName}.las  

log_dbms mode=query project=$env(PG_PROJECT) set=${setName}  well=${wellName} select=_set._all | tp_to_las file_out=${outfile} 

#--------------------------------------------------------------
#set mywells [log_dbms mode=list select=_project well=_all]
#foreach wm $mywells {
#	puts "--> $wm $env(PG_PROJECT)"
#	catch { 
#	log_dbms mode=query project=$env(PG_PROJECT) set=SPLICED well=${wm} select=_set._all | tp_to_las file_out=/peasd/geolog/data/sadah/${wm}_falmd.las 
#	} result 
#	puts "Result -> $result " 

  	#if {[log_exists FALMD set] == 1} {
  		#log_dbms mode = query well = $well set =  FALMD  \
  		#select = ..well_header.field_name ..well_header.well ..well_header.unique_well_id \
			#..well_header.X_LOCATION ..well_header.Y_LOCATION  _set._all \
  		#| tp_to_las file_out = $outdir/$well_falmd.las
	#well_close
 	#}
#}
