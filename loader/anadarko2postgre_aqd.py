# --------------------------------------------------------------------------------
# ASA
# Sontag
# August 2014
# MetOcean conversion to PostGreSQL database for Flex client webservice
#
# Default / user defined variables
# -----------------------------------------------------------------------------------

import sys, time, os, shutil, string, datetime 
import bpgsql as pgs
#import psyco
from sys import argv, exit


# Command prompt
if( len(argv) != 5 ):
    print ""
    print "**    2014 CSV to Postgres"
    print "**"
    print "Please make sure you have the correct number of inputs as below:"
    print "**"
    print "usage: anadarko2postgres <input csv path> <station> <sensorID> <depth>" 
    print "**"
    print "User May need to update database connection if the settings are not the same."
    print "**"     
    print "**"     
    print "** SensorID = ctd,adcp,spectra,awac,tide_gauge,aqd,weather"     
    exit(0)


# Main variables
sensorDict ={"ctd":1,"adcp":2,"spectra":3,"awac":4,"tide_gauge":5,"aqd":6,"weather":7}
workspace = "C:\Users\\ssontag\Desktop\\anadarko_SharedFilesFull\\"
projInfo = "GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]"

s_path = argv[1]
stationID = argv[2]
clientID = 1
sensorID = sensorDict.get(argv[3])
depthval = argv[4]

#-----------------------------------------------------------------------------
# Main Function
#
print
print "***"
print "*** Processing data .... "
print "***"
print
print "Opening file: " + s_path
print "***"


t_name = s_path.replace('.csv','_log.txt')
total_txt = open(t_name, 'w')
localtime = time.asctime( time.localtime(time.time()) )
total_txt.write('logfile for '+s_path +' at '+localtime+'\n\n')


##Edit accordingly
pgconn = pgs.connect(username='postgres',password='PinkPanther#3',host='localhost',port='5432',dbname='oceansmap_obs')
curs = pgconn.cursor()
print "connected to Database, Yay. Now insert records..."

totalRecords=0
a = 0;
startatLine=0;

infile = open(s_path);
inlines = infile.readlines();
infile.close();
for line in inlines:
	
	startatLine+=1  # keep track of lines
	if(startatLine<17):
		print line
	else:
		valuelist = line.split(',');
		#nullchecker= valuelist[4];
		#if nullchecker.find('null',0) ==1:

		print valuelist[0]
		#print "insert into data.data_values(collection_date,station_id,sensor_id,depth,value1,value2,value20,value3) values ('"+valuelist[0]+"',"+str(stationID)+","+str(sensorID)+","+str(depthval)+","+str(valuelist[1])+","+str(valuelist[2])+","+str(valuelist[3])+","+str(1000*float(str(valuelist[4]).replace('\n','')))
		#exit();
		try:
			curs.execute("insert into data.data_values(collection_date,station_id,sensor_id,depth,value1,value2,value20,value3) values ('"+valuelist[0]+"',"+str(stationID)+","+str(sensorID)+","+str(depthval)+","+str(valuelist[1])+","+str(valuelist[2])+","+str(valuelist[3])+","+str(1000*float(str(valuelist[4]).replace('\n','')))+");")
			totalRecords+=1
		except:
			total_txt.write('Error at line: ' +  str(totalRecords) +'\n')  
			break

		if(a>300):
			pgconn.commit()
			a=0;
                

print str(totalRecords)+" total records"
pgconn.commit()
curs.close()
pgconn.close()


print "Total Records: " +  str(totalRecords) +'\n'
total_txt.write('Total Records: ' +  str(totalRecords) +'\n')  
total_txt.write('Completed Successfully.') 

print
print "***"
print "*** Data import and conversion complete."
print "***"

total_txt.close()
sys.exit()