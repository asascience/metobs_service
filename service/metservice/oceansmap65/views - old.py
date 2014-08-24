# Create your views here.
#from django.template import Context, loader
from django.shortcuts import render_to_response, get_object_or_404
#from ctd_j.models import *
from django.http import HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.core.urlresolvers import reverse

import random, string, os, sys
import bpgsql as pgs
from datetime import datetime

import matplotlib
from matplotlib import cm
matplotlib.use('Agg')
import mpl_toolkits.mplot3d.axes3d
import matplotlib.pyplot as plt
from matplotlib import delaunay
from matplotlib.mlab import griddata

# scipy griddata
from scipy import interpolate

import traceback, os.path
#import getpass

from matplotlib.backends.backend_agg import FigureCanvasAgg
from mpl_toolkits.basemap import Basemap

import numpy as np
from numpy import array

import subprocess
from PIL import Image
import re

class customError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

#===============================================================================
# Execute any commandline program and return the result. 
#===============================================================================
def execute(exec_list,out=True,limit_response=0,errors_expected=False,return_proc=False,use_call=False):  
    return_response = []
    
    for cmd in exec_list:
        if out:
            print 'Running  ',' '.join(cmd)
        if use_call:
            res = subprocess.call(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE,stdin=subprocess.PIPE, shell=True)
            return res
        
        local_response = []
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE,stdin=subprocess.PIPE, shell=True)
        stdout_value = proc.communicate()
        
        for value in stdout_value:
            response = value.split('\r\n')
            free_pass = ['ERROR at line 1',                             
                         'Problem running',
                         '',]        
            fail_texts = ['fatal',
                          'ERROR:',
                          'Problem with program execution.'
                          ]
            for r in response:
                if [err for err in fail_texts if err.upper() in r.upper()]:
                    if errors_expected or [err for err in free_pass if err.upper() == r.upper()]:
                        pass
                    else:
                        err_string = '\n'.join(response[response.index(r):])
                        # return_response appears in the stack trace in the test drill down
                        return_response.append(err_string)
                        # print statement shows in the console out for the entire test run
                        print err_string
                if limit_response == 0 or limit_response > len(local_response):
                    local_response.append(r)
                if out:
                    return_response.append(r)
                    print r
    return local_response

#===============================================================================
# KILL PROCESS
#===============================================================================
def tskill(procname):
    'kill all processes based on process name'
    msg = "Failed to kill %s." % procname
    
    exec_list = ([['taskkill','/IM', procname,'/F']])
    msg = execute(exec_list)
        
    return msg

#===============================================================================
# GET PID FROM PROCESS NAME
#===============================================================================
def getPID(procname):
    'Returns PID based on process name'
    exec_list = ([['tasklist']])
    tasklist = execute(exec_list,0)
    pid = ''
    for t in tasklist:
        m = re.search('('+procname+')(.*)(Services|RDP-Tcp#\d)',t)
        if m:
            pid = m.group(2).strip()
            return pid
    return pid

#===============================================================================
# Executes matlab script
#===============================================================================
def runmatlab(request):
    #===========================================================================
    # Set minimum inputs
    #===========================================================================
    try:
        mscript     = request.GET['mscript']
        ncpath      = request.GET['ncpath']
        component   = request.GET['component']
    except:
        return HttpResponse('Invalid minimum inputs. Specify mscript, ncpath, component')
    #===========================================================================
    # Set Stationid
    #===========================================================================
    try:
        stationid   = request.GET['stationid']        
    except:
        stationid   = 'BM30'
    #===========================================================================
    # Set mode
    #===========================================================================
    try:
        mode        = request.GET['mode']
    except:
        mode        = ''
    #===========================================================================
    # Set time domain
    #===========================================================================
    try:
        starttime   = request.GET['starttime']
        endtime     = request.GET['endtime']        
    except:
        starttime   = '04-01-2010'
        endtime     = '10-01-2010'
    #==========================================================================
    # Set depth domain
    #==========================================================================
    try:
        upperdepth  = request.GET['upperdepth']
        lowerdepth  = request.GET['lowerdepth']
    except:
        # if one of these values are not given, following default values will be assigned.
        upperdepth  = '0'
        lowerdepth  = '3000'
    
    
    MatLabPath = 'MATLAB.exe'
#    base = r"C:\development\python\Django\test\matlab"
#    base = r'\\agsdev01\Matlab_ws_scripts'
#    base = r"C:\Program Files (x86)\Apache Software Foundation\Apache2.2\htdocs\matlab_scripts"
    base = 'E:\FTP\matlab_scripts'
    os.chdir(base)
    
    mscriptPath = os.path.join(base,mscript)
    if os.path.isfile(mscriptPath) == False:
        response = HttpResponse("%s not found." % mscript)
    
    # Static name
    filename = 'matlabplot.png'
    # Random name
    #filename = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(18)) + '.png'

    outfile = '"' + os.path.join(base,filename) + '"'
    outfile2 = os.path.join(base,filename)
#    return HttpResponse(outfile)
    
    if os.path.isfile(outfile):
        os.remove(outfile)
    
    #===========================================================================
    # netCDF path
    #===========================================================================
#    ncbase = r"C:\dwh_datasets\CTD"
    ncbase = r"E:\CTD"
    ncpath = os.path.join(ncbase,ncpath)
    
    iomode = ""
    matlab = []
#    sys.path.append(r'C:\Program Files (x86)\MATLAB\R2012a\bin')
    sys.path.append(r'C:\Program Files\MATLAB\R2012a\bin')
#    os.chdir(r'C:\Program Files (x86)\MATLAB\R2012a\bin')
    
    try:
        #=======================================================================
        # FIRST KILL ALL MATLAB JOBS
        #=======================================================================
        msg = tskill(MatLabPath)
        if str(msg).count('SUCCESS'):
            pass
        elif str(msg).count('not found'):
            pass
        else:
            response = HttpResponse(msg)
            return response
        
        #=======================================================================
        # SECOND RUN MATLAB
        #=======================================================================
        matlab.append([MatLabPath,
                         '-nodesktop',
                         '-nosplash',
                         '-minimize',
                         '-noawt',
                         '-r',
                         mscript+"('"+ncpath+"','"+component+"','"+stationid+"','"+starttime+"','"+endtime+"','"+upperdepth+"','"+lowerdepth+"','"+mode+"','"+outfile+"')"])
        
        # This returns value (0 | 1)
#        proc = subprocess.Popen(' '.join(matlab[0]), stdout=subprocess.PIPE,stderr=subprocess.PIPE,stdin=subprocess.PIPE, shell=True)
#        stdout_value = proc.communicate()
#        return HttpResponse('\n'.join(stdout_value))
#        return HttpResponse(' '.join(matlab[0]))

#        result = execute(matlab,use_call=False)
#        return HttpResponse(result)

#        pid = getPID(MatLabPath)
#        if pid != '':
#            return HttpResponse(pid)
#            os.waitpid(int(pid),1)
        
#        res = subprocess.call((matlab[0], stdout=subprocess.PIPE,stderr=subprocess.PIPE,stdin=subprocess.PIPE, shell=True)
#        result = os.system(res)
        os.system(' '.join(matlab[0]))
#        return HttpResponse(result)
        
        import time
        cnt = 0
        while True:
            pid = getPID(MatLabPath)
            if pid != '':
                time.sleep(1)
                cnt+=1
                if cnt == 10: # wait 30sec and break.
                    break
            else:
                break
        
    except Exception, e:
        response = HttpResponse("<b>" + str(e) + ": failed at command execution.</b>")
        return response
    
            
    try:
        if os.path.isfile(outfile2):
            response = HttpResponse(content_type='image/png')
            image = Image.open(outfile2)
#            size = 228, 228
#            image.resize(size)
            image.save(response, "PNG")
            os.remove(outfile2)
        else:
            response = HttpResponse('<b>Image not found</b>')
        
    except Exception, e:
        response = HttpResponse("<b>Failed at response: %s </b>" % str(e))

    finally:
        #=======================================================================
        # FINALLY, KILL ALL MATLAB JOBS
        #=======================================================================
        msg = tskill(MatLabPath)
        if str(msg).count('SUCCESS'):
            pass
        elif str(msg).count('not found'):
            pass
        else:
            response = HttpResponse(msg)
            return response
        return response

#===============================================================================
# Loads & update matlab script metadata
# Description: when the same script name is found, update statement is called.
# When new script name is introduced, insert statement is called.
#
# Example:
# mscript = C:\mylocation\test1.m << This can be just script name.
# arguments = component,startdate,enddate,upperdepth,lowerdepth
# description = This script is a test.
# URL: http://localhost:8080/dwh_serv/ctd_j/loadmatlabscript/?mscriptpath=C:\testdir\test2.m&arguments=component,stationid,starttime,endtime,mode&description=webservice%20test2
#===============================================================================
def loadmatlabscript(request):
    try:
        mscript     = request.GET['mscriptpath']
        arguments   = request.GET['arguments']
        description = request.GET['description']
        mode = request.GET['mode']
        scriptname  = os.path.basename(mscript)
#        description = description.replace('%20', ' ')
    except Exception, e:
        return HttpResponse(str(e))
    
    try:
        pgconn = pgs.connect(username="bio",password="bio",host="localhost",port='5433',dbname="bio")
        curs = pgconn.cursor()
    except:
        return HttpResponse("Sorry, Cannot Connect to Data.")
    
    result = []
    try:
        loaddate = datetime.now()
        loaddate = loaddate.strftime("%Y-%m-%d %H:%M:%S")
#        fileloc = '//agsdev01/Matlab_ws_scripts'
        fileloc = 'E:\FTP\matlab_scripts'
        
        sql = """select script_name from resources.mscript_metadata where script_name = '%s'""" % (scriptname)
        curs.execute(sql)
        result = []
        result = curs.fetchall()
        if len(result) > 0:
            if mode == 'update':
                sql_list = ["""update resources.mscript_metadata set script_desc  = '%s' where script_name = '%s' """ % (description, scriptname),
                            """update resources.mscript_metadata set script_date  = '%s' where script_name = '%s' """ % (loaddate, scriptname),
                            """update resources.mscript_metadata set arguments    = '%s' where script_name = '%s' """ % (arguments, scriptname),
                            """update resources.mscript_metadata set filelocation = '%s' where script_name = '%s' """ % (fileloc, scriptname)
                            ]
                for sql in sql_list:
                    curs.execute(sql)
    
                result = 'Updated: %s, DESC: %s, DATE: %s, FILE: %s, ARGS: %s' % (scriptname, description, loaddate, fileloc, arguments)
            elif mode == 'delete':
                sql = "delete from resources.mscript_metadata where script_name = '%s'" % scriptname
                curs.execute(sql)
                result = 'Deleted: %s' % scriptname
            else:
                result = 'Unknown mode: %s' % mode
        else:
            sql = """insert into resources.mscript_metadata (script_name,script_desc,script_date,filelocation,arguments) values 
         ('%s','%s','%s','%s','%s') """ % (scriptname, description, loaddate, fileloc, arguments)
            curs.execute(sql)
        
            result = 'LOADED: %s, DESC: %s, DATE: %s, FILE: %s, ARGS: %s' % (scriptname, description, loaddate, fileloc, arguments)       
    except Exception, e:
        result.append(str(e) + ' SQL: ' + sql)
    finally:
        curs.close()
        pgconn.close()
        return HttpResponse(result)

#===============================================================================
# Loads file objects on to server. (UNDERDEVELOPMENT)
#===============================================================================
def loadmatlabcode(request):
    try:
        dataDir = "C:\\Program Files (x86)\\Apache Software Foundation\\Apache2.2\\htdocs\\matlab_scripts"
        filepath = os.path.join(dataDir, 'test.txt')  
        received_file = request.FILES['from_flex']
        destination = open(filepath, 'wb+')
        # naively save the file to disk in this case:
        file_data = received_file.read()
        destination.write(file_data)
        destination.close()
        return HttpResponse()
        
    except Exception, e:
        return HttpResponse('Error: '+str(e))
    
#===============================================================================
# Loads matlab script
#===============================================================================
def getmatlabscriptmetadata(request):
    #===========================================================================
    # mscript = C:\mylocation\test1.m
    # arguments = component,startdate,enddate,upperdepth,lowerdepth
    # description = This script is a test.
    #===========================================================================
    try:
        pgconn = pgs.connect(username="bio",password="bio",host="localhost",port='5433',dbname="bio")
        curs = pgconn.cursor()
    except Exception, e:
        return HttpResponse("Sorry, Cannot Connect to Data: " + str(e))
    
    result = []
    try:
        starttime = datetime.now()
        starttime = starttime.strftime("%Y-%m-%d %H:%M:%S")
#        fileloc = '//agsdev01/Matlab_ws_scripts'
        fileloc = 'E:\FTP\matlab_scripts'
        sql = """select script_name, script_desc, to_char(script_date, 'YYYY-MM-DD HH24:MI:SS'), filelocation, arguments from resources.mscript_metadata"""
        curs.execute(sql)
        result = []
        result = curs.fetchall()
        
        result3 = []
        for i in result:
            result2 = []
            for k in i:
                result2.append(str(k))
            result3.append(result2)
        result = result3               
    except Exception, e:
        result.append(str(e) + ' SQL: ' + sql)
    finally:
        curs.close()
        pgconn.close()
        return HttpResponse(result)

#===============================================================================
# Request min & max date of cruise 
#===============================================================================
def getminmaxcruise(request):
    cruise = request.GET['cruise']
    
    try:
        pgconn = pgs.connect(username="ctd",password="ctd",host="localhost",port='5433',dbname="phys2")
        curs = pgconn.cursor()
    except:
        return HttpResponse("Sorry, Cannot Connect to Data.")
    
    sql = """select distinct to_char(min(a.real_time), 'YYYY-MM-DD') as mindate, to_char(max(a.real_time), 'YYYY-MM-DD') as maxdate, b.cruise from ctd.stations a, ctd.cruises b where a.station = b.station and b.cruise = '%s' group by b.cruise""" % cruise
    
    try:
        curs.execute(sql)
        cruiseData = []
        fetchData = []
        fetchData = curs.fetchall()
        if len(fetchData) == 0:
            return HttpResponse("Failed to retrieve data for %s: %s" % (cruise,sql))
        else:
            for i in fetchData:
                result2 = []
                for k in i:
                    result2.append(str(k))
                cruiseData.append(result2)            
            return HttpResponse(str(cruiseData[0]).replace(" '",'').replace("'",''))
    except Exception, e:
        et, ev, tb = sys.exc_info()
        lineno = " - Error Line #: " + str(traceback.tb_lineno(tb))
        return HttpResponse(str(e) + ' SQL: ' + sql + lineno)
    finally:
        curs.close()
        pgconn.close()
    
    

#===============================================================================
# Request ESRI shapefile extraction and return file URL
#===============================================================================
def getshpfile(request):     
    attr = request.GET['attr']
    depthindex = request.GET['depthindex']
    mindepth = request.GET['mindepth']
    maxdepth = request.GET['mindepth']
    startTime = request.GET['startTime']
    endTime = request.GET['endTime']
    polygon = request.GET['polygon']
    
#    attr='a',depthindex='a',startTime='2006-01-01',endTime='2012-01-01',polygon=[]

    if(depthindex not in ['min','max','mean','distinct']):
        if (depthindex == "all"):
            depthindex = '0'
        sql = """select stations.s_id,stations.pt_geom,stations.real_time,%s.value,%s.units,%s.depth,%s.station station from stations,%s where %s.depthid = %s and %s.depth IS NOT NULL and %s.s_id = stations.s_id and stations.real_time >= '%s' and stations.real_time <= '%s' and ST_Contains(ST_GeomFromText(\'polygon((%s))\',4326),stations.pt_geom)""" % (attr,attr,attr,attr,attr,attr,depthindex,attr,attr,startTime,endTime,polygon)

    elif (depthindex == 'distinct'):
        sql = """select stations.s_id,stations.pt_geom,stations.real_time,%s.value,%s.units,%s.depth,%s.station station from stations,%s where %s.depthid >= %s and %s.depthid <= %s and %s.depth IS NOT NULL and %s.s_id = stations.s_id and stations.real_time >= '%s' and stations.real_time <= '%s' and ST_Contains(ST_GeomFromText(\'polygon((%s))\',4326),stations.pt_geom)""" % (attr,attr,attr,attr,attr,attr,mindepth,attr,maxdepth,attr,attr,startTime,endTime,polygon)
       
    elif (depthindex == 'max'):
        sql = """select distinct stations.lat,stations.long,stations.time,stations.station, max.maxvalue, stations.s_id, %s.depth, stations.pt_geom from stations, %s, (select s_id, max(%s.value) as maxvalue from %s where time >= '%s' and time <= '%s' group by s_id) max where stations.s_id=%s.s_id and %s.s_id = max.s_id and stations.real_time >= '%s' and stations.real_time <= '%s' and %s.value = max.maxvalue and ST_Contains(ST_GeomFromText(\'polygon((%s))\',4326),stations.pt_geom) group by stations.lat,stations.long,stations.time,stations.station,max.maxvalue,stations.s_id, %s.depth, stations.pt_geom order by stations.s_id""" % (attr, attr, attr, attr, startTime, endTime, attr, attr, startTime, endTime, attr, polygon, attr)
        
    elif (depthindex == 'min'):
        sql = """select distinct stations.lat,stations.long,stations.time,stations.station, min.minvalue, stations.s_id, %s.depth, stations.pt_geom from stations, %s, (select s_id, min(%s.value) as minvalue from %s where time >= '%s' and time <= '%s' group by s_id) min where stations.s_id = %s.s_id and %s.s_id = min.s_id and stations.real_time >= '%s' and stations.real_time <= '%s' and %s.value = min.minvalue and ST_Contains(ST_GeomFromText(\'polygon((%s))\',4326),stations.pt_geom) group by stations.lat,stations.long,stations.time,stations.station,min.minvalue,stations.s_id, %s.depth, stations.pt_geom order by stations.s_id""" % (attr, attr, attr, attr, startTime, endTime, attr, attr, startTime, endTime, attr, polygon, attr)

    elif (depthindex == 'mean'):
        sql = """select distinct stations.lat,stations.long,stations.time,stations.station, mean.meanvalue, stations.s_id, stations.pt_geom from stations, %s, (select s_id, avg(%s.value) as meanvalue from %s where time >= '%s' and time <= '%s' group by s_id) mean where stations.s_id=%s.s_id and stations.s_id = mean.s_id and stations.real_time >= '%s' and stations.real_time <= '%s' and ST_Contains(ST_GeomFromText(\'polygon((%s))\',4326),stations.pt_geom) group by stations.lat,stations.long,stations.time,stations.station,mean.meanvalue,stations.s_id, stations.pt_geom""" % (attr, attr, attr, startTime, endTime, attr, startTime, endTime, polygon)

    try:
        #=======================================================================
        # Using postgres2shp function for sql select taking in a polygon download using a random file name and zipping the folder
        # Example polygon query -89.4 28.8, -87.7 28.8, -89.4 27.8, -87.7 27.8, -89.4 28.8
        #=======================================================================
        dataDir = "C:\\Program Files (x86)\\Apache Software Foundation\\Apache2.2\\htdocs\\ctd_download"
        os.chdir(dataDir)

        newfolder = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(18))
        os.mkdir(newfolder)
        filename = "ctd_"+attr+"_"+startTime+"_"+endTime+"_depth_"+depthindex+".shp"
        
        outputpath = os.path.join(dataDir, newfolder, filename)
#        cmd = """C:\\ctd\\app\\service\\pgsql2shp.exe -f \""""+outputpath+'" -h localhost -p 5433 -u ctd -P ctd phys2 "'+sql+"\""
#        os.system("""C:\\ctd\\app\\service\\pgsql2shp.exe -f \""""+outputpath+'" -h localhost -p 5433 -u ctd -P ctd phys2 "'+sql+"\"")
#        cmd = """"C:\\Program Files\\PostgreSQL\\9.1\\bin\\pgsql2shp.exe" -f \""""+outputpath+'" -h localhost -p 5433 -u ctd -P ctd phys2 "'+sql+"\""
        os.system(""""\"C:\\Program Files\\PostgreSQL\\9.1\\bin\\pgsql2shp.exe" -f \""""+outputpath+'" -h localhost -p 5433 -u ctd -P ctd phys2 "'+sql+"\"")
        os.system("\"C:\\Program Files (x86)\\7-Zip\\7z.exe\" a -tzip "+newfolder+".zip "+newfolder)

        import glob
        if os.path.isfile(os.path.join(dataDir,newfolder,filename)):
            files = glob.glob(os.path.join(dataDir,newfolder,"*"))
            for file in files:
                os.remove(file)
        os.removedirs(os.path.join(dataDir,newfolder))
        
        return HttpResponse("http://dwh.asascience.com:8080/ctd_download/"+newfolder+".zip")
    except Exception , e:
        return HttpResponse("Sorry, Cannot return Shapefile DataFile. " + str(e))

#===============================================================================
# Request CSV file extraction and return file URL
#===============================================================================
def getcsvfile(request):        
#    attr='a',depthindexStart='a',depthindExend='a',startTime='2006-01-01',endTime='2012-01-01',valuemin='a',valuemax='a'
    attr = request.GET['attr']
    depthindex = request.GET['depthindex']
    startTime = request.GET['startTime']
    endTime = request.GET['endTime']
    polygon = request.GET['polygon']
    whereclause = request.GET['whereclause']
    sql = ""
    
    try:
        pgconn = pgs.connect(username="ctd",password="ctd",host="localhost",port='5433',dbname="phys2")
        curs = pgconn.cursor()
    except:
        return HttpResponse("Sorry, Cannot Connect to Data.")
    
    try:
        ##Using COPY function for sql select taking in a attributes to csv download
        dataDir = r"C:\\Program Files (x86)\Apache Software Foundation\Apache2.2\htdocs\ctd_download"
        os.chdir(dataDir)
        
        newfolder = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(15))
        os.mkdir(newfolder)
        filename = "ctd_"+attr+"_depth_"+depthindex+"_"+startTime+"_"+endTime+".csv"
        
        fileoutput = os.path.join(dataDir,newfolder,filename)

        if(depthindex not in ['min','max','mean']):
            if (depthindex == "all"):
                depthindex = '0'
            sql = """select stations.s_id, stations.real_time as date, %s.value as value, %s.units, %s.depth, stations.station station from stations,%s where %s.depthid = %s and %s.depth IS NOT NULL and %s.s_id = stations.s_id and stations.real_time >= '%s' and stations.real_time <= '%s' and ST_Contains(ST_GeomFromText(\'polygon((%s))\',4326),stations.pt_geom)""" % (attr,attr,attr,attr,attr,depthindex,attr,attr,startTime,endTime,polygon)

        elif (depthindex == 'max'):
            sql = """select distinct stations.s_id, stations.time as date, max.maxvalue as value, %s.units, %s.depth, stations.station from stations, %s, (select s_id, max(%s.value) as maxvalue from %s where time >= '%s' and time <= '%s' group by s_id) max where stations.s_id=%s.s_id and %s.s_id = max.s_id and stations.real_time >= '%s' and stations.real_time <= '%s' and %s.value = max.maxvalue and ST_Contains(ST_GeomFromText(\'polygon((%s))\',4326),stations.pt_geom) group by stations.lat,stations.long,stations.time,stations.station,max.maxvalue,stations.s_id, %s.depth, stations.pt_geom order by stations.s_id""" % (attr, attr, attr, attr, attr, startTime, endTime, attr, attr, startTime, endTime, attr, polygon, attr)
            
        elif (depthindex == 'min'):
            sql = """select distinct stations.s_id, stations.time as date, min.minvalue as value, %s.units, %s.depth, stations.station from stations, %s, (select s_id, min(%s.value) as minvalue from %s where time >= '%s' and time <= '%s' group by s_id) min where stations.s_id = %s.s_id and %s.s_id = min.s_id and stations.real_time >= '%s' and stations.real_time <= '%s' and %s.value = min.minvalue and ST_Contains(ST_GeomFromText(\'polygon((%s))\',4326),stations.pt_geom) group by stations.lat,stations.long,stations.time,stations.station,min.minvalue,stations.s_id, %s.depth, stations.pt_geom order by stations.s_id""" % (attr, attr, attr, attr, attr, startTime, endTime, attr, attr, startTime, endTime, attr, polygon, attr)
    
        elif (depthindex == 'mean'):
            sql = """select distinct stations.s_id, stations.time as date, mean.meanvalue as value, %s.units, %s.depth, stations.station from stations, %s, (select s_id, avg(%s.value) as meanvalue from %s where time >= '%s' and time <= '%s' group by s_id) mean where stations.s_id=%s.s_id and stations.s_id = mean.s_id and stations.real_time >= '%s' and stations.real_time <= '%s' and ST_Contains(ST_GeomFromText(\'polygon((%s))\',4326),stations.pt_geom) group by stations.lat,stations.long,stations.time,stations.station,mean.meanvalue,stations.s_id, stations.pt_geom""" % (attr, attr, attr, attr, attr, startTime, endTime, attr, startTime, endTime, polygon)


        curs.execute("COPY ("+sql+") TO '"+ fileoutput+"""' WITH CSV HEADER DELIMITER ',' QUOTE AS '"'""")

        # ORIG
        #curs.execute("COPY (select "+attr+".value,"+attr+".units,stations.station,stations.real_time,"+attr+".depth from stations,"+attr+" where "+attr+".s_id = stations.s_id and "+attr+".depthid < "+depthindExend+" and "+attr+".depthid > "+depthindexStart+"and "+attr+".value < "+valuemax+" and "+attr+".value > "+valuemin+" and stations.real_time > '"+startTime+"' and stations.real_time<'"+endTime+"') TO '"+ fileoutput+"""' WITH CSV HEADER DELIMITER ',' QUOTE AS '"'""")
        #return "http://24.249.210.121:8080/ctd_download/"+"ctd_"+attr+"_depth_"+depthindexStart+"_"+startTime+".csv"
                    
        os.system("\"C:\\Program Files (x86)\\7-Zip\\7z.exe\" a -tzip "+newfolder+".zip "+newfolder+ " -mx9")
#        os.remove(newfolder)
        
        return HttpResponse("http://dwh.asascience.com:8080/ctd_download/"+newfolder+".zip")

    except Exception, Err:
        curs.close()
        pgconn.close()
        return HttpResponse("Sorry, Cannot return Downloaded CSV DataFile. " + str(Err) + "| SQL: " + sql)
        
#===============================================================================
# GetCTDValues
# Description: User requests stationid (BM30) and attribute type (temperature)
# and returnes records with location.
#===============================================================================
def getctdvalues(request):
    statname = request.GET['station']
    attrtype = request.GET['attrtype']
    try:
        mindepth = request.GET['mindepth']
        maxdepth = request.GET['maxdepth']
        if mindepth == '':
            mindepth = 0
            maxdepth = 5000        
    except:
        mindepth = 0
        maxdepth = 5000
        
    try:
        pgconn = pgs.connect(username="ctd",password="ctd",host="localhost",port='5433',dbname="phys2")
        curs = pgconn.cursor()
    except:
        return HttpResponse("Sorry, Cannot Connect to Data.")
    
    try:
        sql = "select a.value::numeric,a.time,a.units,a.depthid,a.depth,a.qc,b.lat,b.long from "+ attrtype+" a, stations b where a.station = b.station and a.station = '"+statname+"' and a.depthid >= "+str(mindepth)+" and a.depthid <= "+str(maxdepth)+" and value IS NOT NULL;"
#        sql = "select value,time,units,depthid,depth, qc from "+ attrtype+" where station = '"+statname+"' and depthid >= "+str(mindepth)+" and depthid <= "+str(maxdepth)+" and value IS NOT NULL;"
        curs.execute(sql)
        stationData = []
        stationData = curs.fetchall()
        curs.close()
        pgconn.close()
#        return HttpResponse(sql)
        return HttpResponse(str(stationData))
    except Exception, e:
        curs.close()
        pgconn.close()
        return HttpResponse("Sorry, Cannot return station Data: " + str(e))

#===============================================================================
# GetBufferPoly
#===============================================================================
def getbufferpoly(request):
    whereclause=request.GET['whereclause']
    try:
        pgconn = pgs.connect(username="ctd",password="ctd",host='localhost',port='5433',dbname="phys2")
        curs = pgconn.cursor()
    except:
        return HttpResponse("Sorry, Cannot Connect to Data.")
    
    try:
        sql = "select ST_AsText(%s )as buffer" % whereclause
        curs.execute(sql)
        coords = []
        coords = curs.fetchall()
        curs.close()
        pgconn.close()
        bufferpoly = ""
        if len(coords) <> 1:
            return HttpResponse("Sorry, Cannot return coordinates." + str(len(coords)))
        else:
            bufferpoly = str(coords[0]).replace("[u'POLYGON((","")
            bufferpoly = bufferpoly.replace("))']","")
            return HttpResponse(bufferpoly)
        return HttpResponse(str(coords))
    except Exception, Err:
        curs.close()
        pgconn.close()
        return HttpResponse("Sorry, Cannot return coordinates." + str(Err))
        
#===========================================================================
# attr can be: all, depth, direction, speed
# If attr is all, it uses station_groups table to display unique stations.
# If attr is specified, it uses adcp_attr table to query based on attr values.
#===========================================================================        
def getadcpstations(request):  
    depth = request.GET['depth']
    startTime = request.GET['startTime']
    endTime = request.GET['endTime'] 
    try:
        depth_interval = request.GET['depthInterval']
    except:
        depth_interval = '20'
         
    try:
        pgconn = pgs.connect(username="phys",password="phys",host="localhost",port='5433',dbname="phys2",schema='adcp')
        curs = pgconn.cursor()
    except:
        return HttpResponse("Sorry, Cannot Connect to Data.")
    try:
        
        if depth == 'all':
            #===============================================================
            # query station table
            #===============================================================
            sql = """
            select distinct stationid, lat, long
            from
            adcp.station_groups
            where date >= '%s' and date <= '%s'
            """ % (startTime, endTime)

        #=======================================================================
        # Disenabled since they can be controled by depth slider 
        #=======================================================================
#        elif depth == 'min':
#
#            sql = """
#            select distinct stationid, lat, long from adcp.station_groups
#            where stationid in (select stationid from adcp.adcp_attr where date >= '%s' and date <= '%s' 
#            and depth in (select min(depth) from adcp.adcp_attr where date >= '%s' and date <= '%s'))
#            """ % (startTime, endTime, startTime, endTime)
#
#        elif depth == 'max':
#
#            sql = """
#            select distinct stationid, lat, long from adcp.station_groups
#            where stationid in (select stationid from adcp.adcp_attr where date >= '%s' and date <= '%s' 
#            and depth in (select max(depth) from adcp.adcp_attr where date >= '%s' and date <= '%s'))
#            """ % (startTime, endTime, startTime, endTime)
#
#        elif depth == 'mean':
#
#            sql = """
#            select distinct stationid, lat, long from adcp.station_groups
#            where stationid in (select stationid from adcp.adcp_attr where date >= '%s' and date <= '%s' 
#            and depth >= (select round(avg(depth))-5 from adcp.adcp_attr where date >= '%s' and date <= '%s') 
#            and depth <= (select round(avg(depth))+5 from adcp.adcp_attr where date >= '%s' and date <= '%s'))
#            """ % (startTime, endTime, startTime, endTime, startTime, endTime)
                            
        else:
            #===============================================================
            # Query nearest depth value (if approx depth is specified)
            #===============================================================
#            sql = """
#            select a.stationid, a.lat, a.long, a.nearest_depth, a.speed, a.direction, to_char(a.date, 'YYYY-MM-DD HH24:MI:SS') as date from
#            (select distinct stationid, lat, long, abs(depth - %s) as nearest_depth, speed, direction, date
#            from adcp.adcp_attributes
#            where date = '%s' 
#            and abs(depth - %s) <= 100
#            order by stationid) a,
#            (select distinct stationid, min(abs(depth - %s)) as nearest_depth
#            from adcp.adcp_attributes 
#            where date = '%s' 
#            and abs(depth - %s) <= 100
#            group by stationid) b
#            where a.stationid = b.stationid and a.nearest_depth = b.nearest_depth;
#            """ % (depth, startTime, depth, depth, startTime, depth)
            
            #===================================================================
            # Depth interval
            #===================================================================
#            sql = """
#            select a.stationid, c.lat, c.long, a.nearest_depth, a.speed, a.direction, 
#            to_char(a.date, 'YYYY-MM-DD HH24:MI:SS') as date 
#            from 
#            (select distinct stationid, abs(depth - %s) as nearest_depth, speed, direction, date from adcp.adcp_attr where date = '%s' and abs(depth - %s) <= %s) a, 
#            (select distinct stationid, lat, long from adcp.station_groups) c 
#            where 
#            a.stationid = c.stationid
#            and a.speed <> -999 and a.direction <> -999 order by a.nearest_depth
#            """ % (depth, startTime, depth, depth_interval)
            
            #===================================================================
            # Depth buffer +- buffer (default 20m)
            #===================================================================
            sql = """
            select a.stationid, c.lat, c.long, a.depth, a.speed, a.direction, 
            to_char(a.date, 'YYYY-MM-DD HH24:MI:SS') as date 
            from 
            (select distinct stationid, depth, speed, direction, date from adcp.adcp_attr where date = '%s' and depth >= (%s - %s) and depth <= (%s + %s)) a, 
            (select distinct stationid, lat, long from adcp.station_groups) c 
            where 
            a.stationid = c.stationid
            and a.speed <> -999 and a.direction <> -999 order by a.depth
            """ % (startTime, depth, depth_interval, depth, depth_interval)
            
        curs.execute(sql)
        stationData = []
        stationData = curs.fetchall()
#        return HttpResponse(sql)
        return HttpResponse(str(stationData))  
    
    except Exception, Err:
        return HttpResponse("Sorry, Cannot return stations. " + str(Err))  
    finally:
        curs.close()
        pgconn.close()

#===============================================================================
# GetADCPValues: Search ADCP based on stationid, depth and/or date.
#===============================================================================
def getadcpvalues(request):
    stationid = request.GET['stationid']
    depth = request.GET['depth']
    startTime = request.GET['startTime']
    endTime = request.GET['endTime']
    limit = request.GET['limit']
    try:
        depth_interval = request.GET['depthInterval']
    except:
        depth_interval = '10'
        
    try:
        pgconn = pgs.connect(username="phys",password="phys",host="localhost",port='5433',dbname="phys2",schema='adcp')
        curs = pgconn.cursor()
    except:
        return HttpResponse("Sorry, Cannot Connect to Data.")
    
    try:
        # set limit to large number if it is 'all'.
        if limit == 'all':
            limit = 1000000

        #===============================================================
        # Query for all stations
        #===============================================================
        if(stationid == 'all'):
            sql = """
            select distinct stationid, direction, speed, depth, to_char(date, 'YYYY-MM-DD HH24:MI:SS') as date
            from
            adcp.adcp_attr
            where date >= '%s' and date <= '%s' and (direction is not null or speed is not null)
            and (direction is not -999)
            and stationid = %s
            order by date
            limit %s
            """ % (startTime, endTime, stationid, limit)
            
        
        elif depth == 'all':
            #===============================================================
            # Query with stationid
            #===============================================================
#            sql = """
#            select distinct stationid, direction, speed, depth, to_char(date, 'YYYY-MM-DD HH24:MI:SS') as date
#            from
#            adcp.adcp_attr
#            where date >= '%s' and date <= '%s' and stationid = %s
#            and (direction is not null or speed is not null) 
#            and (direction <> -999)
#            order by date
#            limit %s
#            """ % (startTime, endTime, stationid, limit)
            
            #===================================================================
            # Depth buffer +- buffer
            #===================================================================
            sql = """
            select stationid, direction, speed, depth, to_char(date, 'YYYY-MM-DD HH24:MI:SS') as date 
            from adcp.adcp_attr 
            where date >= '%s' and date <= '%s' and mod(depth::Integer,200) = 0
            and speed <> -999 and direction <> -999 
            and stationid = %s order by date
            """ % (startTime, endTime, stationid)
            

#        elif depth == 'min':
#            sql = """
#            select distinct a.stationid, b.direction, b.speed, b.depth, to_char(b.date, 'YYYY-MM-DD HH24:MI:SS') as date
#            from adcp.station_groups a, adcp.adcp_attr b
#            where a.stationid = b.stationid
#            and a.date >= '%s' and a.date <= '%s' and (direction is not null or speed is not null) 
#            and (direction < -999)
#            and b.depth = (select min(depth) from adcp_attr where date >= '%s' and date <= '%s') 
#            order by date
#            limit %s
#            """ % (startTime, endTime, startTime, endTime, limit)
#
#
#        elif depth == 'max':
#            sql = """
#            select distinct a.stationid, b.direction, b.speed, b.depth, to_char(b.date, 'YYYY-MM-DD HH24:MI:SS') as date
#            from adcp.station_groups a, adcp.adcp_attr b
#            where a.stationid = b.stationid
#            and a.date >= '%s' and a.date <= '%s' and (direction is not null or speed is not null)
#            and (direction < -999) 
#            and b.depth = (select max(depth) from adcp_attr where date >= '%s' and date <= '%s') 
#            order by date
#            limit %s
#            """ % (startTime, endTime, startTime, endTime, limit)
#
#        
#        elif depth == 'mean':
#            sql = """
#            select distinct a.stationid, b.direction, b.speed, b.depth, to_char(b.date, 'YYYY-MM-DD HH24:MI:SS') as date
#            from adcp.station_groups a, adcp.adcp_attr b
#            where a.stationid = b.stationid
#            and b.depth >= (select avg(depth)-5 from adcp_attr c where date >= '%s' and date <= '%s')
#            and b.depth <= (select avg(depth)+5 from adcp_attr c where date >= '%s' and date <= '%s')
#            and a.date >= '%s' and a.date <= '%s' and (direction is not null or speed is not null)
#            and (direction <> -999) 
#            order by date 
#            limit %s
#            """ % (startTime, endTime, startTime, endTime, startTime, endTime, limit)

        else:
            #===============================================================
            # Query with nearest depth value
            #===============================================================
#            sql = """
#            select distinct stationid, direction, speed, depth, to_char(date, 'YYYY-MM-DD HH24:MI:SS') as date, abs(depth - %s) as nearest_depth
#            from adcp.adcp_attr  
#            where date >= '%s' and date <= '%s' and stationid = %s
#            and (direction is not null or speed is not null)
#            and direction <> -999
#            order by nearest_depth 
#            limit %s
#            """ % (depth, startTime, endTime, stationid, limit)
            
            #===================================================================
            # Depth buffer +- buffer
            #===================================================================
            sql = """
            select stationid, direction, speed, depth, to_char(date, 'YYYY-MM-DD HH24:MI:SS') as date
            from adcp.adcp_attr 
            where date >= '%s' and date <= '%s'  and depth >= (%s - %s) and depth <= (%s + %s)
            and speed <> -999 and direction <> -999 
            and stationid = %s order by date limit %s
            """ % (startTime, endTime, depth, depth_interval, depth, depth_interval, stationid, limit)
            
        #===============================================================
        # Execute query
        #===============================================================    
        curs.execute(sql)
        stationData = []
        stationData = curs.fetchall()
#        return HttpResponse(sql) 
        return HttpResponse(str(stationData))  
    
    except Exception, Err:
        return HttpResponse("Sorry, Cannot return stations. " + str(Err) + " " + sql)
    finally:
        curs.close()
        pgconn.close()

#===============================================================================
# Get variable count stats of given station.
#===============================================================================
def getstationstats(request):
    station = request.GET['stationid']

    try:
        pgconn = pgs.connect(username="ctd",password="ctd",host="localhost",port='5433',dbname="phys2")
        curs = pgconn.cursor()
    except:
        return HttpResponse("Sorry, Cannot Connect to Data.")   
    
    d = {}
    variables = ['cdom_eco', 'cdom_wetlab', 'cor_chl_fl', 'density', 'do_mass', 'do_vol', 'hc_fl', 'hc_fl_aqua', 'salinity', 'scufa_fl', 'temperature', 'cdom_eco_anom', 'cdom_wetlab_anom']
    
    sql = """
select a.cnt, b.cnt, c.cnt, d.cnt, e.cnt, f.cnt, g.cnt, h.cnt, i.cnt, j.cnt, k.cnt, l.cnt, m.cnt
from
(select count(*) as cnt from ctd.cdom_eco where station = '%s' and value IS NOT NULL) a,
(select count(*) as cnt from ctd.cdom_wetlab where station = '%s' and value IS NOT NULL) b,
(select count(*) as cnt from ctd.cor_chl_fl where station = '%s' and value IS NOT NULL) c,
(select count(*) as cnt from ctd.density where station = '%s' and value IS NOT NULL) d,
(select count(*) as cnt from ctd.do_mass where station = '%s' and value IS NOT NULL) e,
(select count(*) as cnt from ctd.do_vol where station = '%s' and value IS NOT NULL) f,
(select count(*) as cnt from ctd.hc_fl where station = '%s' and value IS NOT NULL) g,
(select count(*) as cnt from ctd.hc_fl_aqua where station = '%s' and value IS NOT NULL) h,
(select count(*) as cnt from ctd.salinity where station = '%s' and value IS NOT NULL) i,
(select count(*) as cnt from ctd.scufa_fl where station = '%s' and value IS NOT NULL) j,
(select count(*) as cnt from ctd.temperature where station = '%s' and value IS NOT NULL) k,
(select count(*) as cnt from ctd.cdom_eco_anom where station = '%s' and value IS NOT NULL) l,
(select count(*) as cnt from ctd.cdom_wetlab_anom where station = '%s' and value IS NOT NULL) m;
    """ % (station, station, station, station, station, station, station, station, station, station, station, station, station)
    
    try:
        curs.execute(sql)
        results = curs.fetchall()
        cnt = 0
        for elem in variables:
            d[elem] = str(results[0][cnt])
            cnt+=1
        return HttpResponse(str(d).replace("{",'').replace("}",''))
    except Exception, e:
        return HttpResponse(str(e))
    finally:
        curs.close()
        pgconn.close()
        
#===============================================================================
# GetCruises: request unique cruise names
#===============================================================================
def getcruises(request):
    try:
        pgconn = pgs.connect(username="ctd",password="ctd",host="localhost",port='5433',dbname="phys2")
        curs = pgconn.cursor()
    except:
        return HttpResponse("Sorry, Cannot Connect to Data.")
    
    getallcruise = True;
    stationid = ''
    try:
        getallcruise = False;
        stationid = request.GET['stationid']
    except:
        getallcruise = True;
        pass
    
    try:
        cruises = []
        if getallcruise == True:
            sql = "select distinct cruise from cruises order by cruise;"
        else:
            sql = "select distinct cruise from cruises where station = '%s'" % stationid
        curs.execute(sql)
        results = curs.fetchall()
        for i in results:
            target = str(i[0]).strip()
            if getallcruise == True:
                cruises.append(target)
            else:
                cruises.append(target.replace(' ','_') + ".nc")
    except Exception, e:
        cruises = str(e)
    finally:
        curs.close()
        pgconn.close()
        return HttpResponse(str(cruises))

 
#===============================================================================
# GetLocation: Get location based on stationid
#===============================================================================
def getlocation(request):
    stationid = request.GET['stationid']
    import re
    if re.search('[A-Z]',stationid) == None:
        # ADCP
        user="phys"
        pwd="phys"
        db="phys2"
        sql = "select distinct long, lat, stationid from adcp.station_groups where stationid = %s;" % str(stationid)    
    else:
        # CTD
#        user="postgres"
#        pwd="postGre@2"
#        db="ctd"
        user="ctd"
        pwd="ctd"
        db="phys2"
        sql = "select distinct long, lat, station from ctd.stations where station = '%s';" % str(stationid)
    
    try:
        pgconn = pgs.connect(username=user,password=pwd,host='localhost',port='5433',dbname=db)
        curs = pgconn.cursor()
    except:
        return HttpResponse("Sorry, Cannot Connect to Data.")
    
    try:
        curs.execute(sql)
        coords = []
        coords = curs.fetchall()
        return HttpResponse(str(coords))
    except Exception, Err:
        return HttpResponse("Sorry, Cannot return coordinates for %s: %s" % (str(stationid),Err.message))
    finally:
        curs.close()
        pgconn.close()
        
#===============================================================================
# Request stations and return lat,long, time and station_names
# default to all available dates and data
#===============================================================================
def getstations(request):
    attr = request.GET['attr']
    depthindex = request.GET['depthindex']
    startTime = request.GET['startTime']
    endTime = request.GET['endTime']
    mode = request.GET['mode']
    whereclause = request.GET['whereclause']
    
    #===========================================================================
    # Get min/max depth
    #===========================================================================
    try:
        mindepth = request.GET['mindepth']
        maxdepth = request.GET['maxdepth']
    except:
        mindepth = depthindex
        maxdepth = str(int(depthindex) + 10)
    
    try:
        bbox = request.GET['BBOX']  
        bbox = bbox.split(',')      
    except:
        bbox = ""

    if bbox == "":
        bbox =",,,"
        bbox = bbox.split(',')
    
    lonmin = bbox[0]
    latmin = bbox[1]
    lonmax = bbox[2]
    latmax = bbox[3]
    
    # VERTICAL PROFILE DEPTH INTERVAL
    try:
        depthInterval = request.GET['depthInterval']
    except:
        depthInterval = 200
        
    ## JF 6/8/12 - Adding interpolation option that can be passed to vertical profile service.
    # VERTICAL PROFILE INTERPOLATION METHOD
    try:
        interp_method = request.GET['interpMethod']
    except:
        interp_method = 'linear'
        
    # Horizontal Interpolation width/height
    try:
        mapwidth = request.GET['WIDTH']
        mapheight = request.GET['HEIGHT']
        if mapwidth == "":
            mapwidth = 1750
            mapheight = 880
    except:
        mapwidth = 1750
        mapheight = 880
    
    # Horizontal Interpolation style
    try:
        style = request.GET['style']
        if style == "":
            style = 'rainbow'
    except:
        style = 'rainbow'
    
    # Horizontal Interpolation min/max
    try:
        zmin = request.GET['zmin']
        zmax = request.GET['zmax']
    except:
        zmin=None 
        zmax=None
        
    if style == "":
        style = 'rainbow'
    
    response = HttpResponse(content_type='image/png')
    
    #===========================================================================
    # DB Connection.
    #===========================================================================
    try:
        pgconn = pgs.connect(username="ctd",password="ctd",host="localhost",port='5433',dbname="phys2")
        curs = pgconn.cursor()
    except:
        return HttpResponse("Sorry, Cannot Connect to Data.")
    
    
    dist_query = ''
    dist_order = ''
    sql = ''
    stationData = []

#    if whereclause <> '':
    if mode in ['2dvquery','3dvquery']:
        if whereclause.count("ST_GeomFromText"):
            dist_query = "ST_GeomFromText"+ whereclause.split("ST_GeomFromText")[1].split(",4326)")[0]

            #distance (m) from start point to all stations.
            dist_query = ", ST_Line_Locate_Point(%s,4326), stations.pt_geom) * ST_Length(%s,4326)) as dist" % (dist_query, dist_query)
            dist_order = ", dist order by dist"
        whereclause = " and " + whereclause #+ " and " + attr+".qc < 3"
        whereclause = whereclause.replace("0#","0.")
##        else:
##            whereclause = " and " + attr+".qc < 3"
        
    try:            
        if(attr == 'a'):
            curs.execute("select lat,long,time,station,s_id from stations;")
            stationData = curs.fetchall()

        elif mode in ['2dvquery','3dvquery']: #if(depthindex in ['all','surface_level']):
            orig_dist_order = dist_order
            dist_order = dist_order.replace(", dist"," ")  # other queries needs ', dist' for group by.
            filename = ''
            errorfile = "http://dwh.asascience.com:8080/ctd_download/vprofile/no_image_404.png"

            #GET SURFACE LEVEL VALUES:
            sql = """
            select distinct stations.lat,stations.long,stations.time,stations.station,%s.value::numeric,stations.s_id,%s.depth %s
            from stations, %s where stations.s_id=%s.s_id and %s.depthid = 0
            and stations.real_time >= '%s' and stations.real_time <= '%s' %s
            """ % (attr, attr, dist_query, attr, attr, attr, startTime, endTime, whereclause)
            curs.execute(sql)
            stationData = curs.fetchall()
            

            #GET ALL DEPTH LEVEL VALUES: LIMITED TO depthid (integer) mod 200
            #if mode in ['2dvquery','3dvquery']:
            stationDataAll = []
            sql = """
            select stations.lat,stations.long,stations.time,stations.station,%s.value,stations.s_id,%s.depth %s
            from stations, %s where stations.s_id=%s.s_id and (%s.value is not null or %s.depth is not null)
            and mod(%s.depthid,%s) = 0
            and stations.real_time >= '%s' and stations.real_time <= '%s' %s %s
            """ % (attr, attr, dist_query, attr, attr, attr, attr, attr, depthInterval, startTime, endTime, whereclause, dist_order)

            curs.execute(sql)
            stationDataAll = curs.fetchall()

            # Graph vertical profile and return its filename.
            if len(stationData) > 2:
                ## JF 6/8/11 - Added interp method to vprofile call
                filename = plot_vprofile(stationDataAll, mode, attr, style, interp_method)
            if filename <> '':
                stationData.append(filename)
            else:
                stationData.append(errorfile)
            
        
        elif (depthindex == 'max'):
            sql = """
            select distinct stations.lat,stations.long,stations.time,stations.station, max.maxvalue::numeric, stations.s_id, %s.depthid %s
            from 
            stations, 
            %s, 
            (select distinct s_id, station, max(%s.value) as maxvalue from %s where %s.depthid >= %s and %s.depthid <= %s group by s_id, station) max
            where 
            stations.s_id=%s.s_id 
            and %s.s_id = max.s_id
            and stations.station = %s.station
            and stations.station = max.station
            and stations.real_time >= '%s' and stations.real_time <= '%s'
            and %s.depthid >= %s and %s.depthid <= %s
            and %s.value = max.maxvalue %s
            group by stations.lat,stations.long,stations.time,stations.station,max.maxvalue,stations.s_id, %s.depthid %s
            """ % (attr, dist_query, 
                   attr, 
                   attr, attr, attr, mindepth, attr, maxdepth, 
                   attr, 
                   attr, 
                   attr, 
                   startTime, endTime, 
                   attr, mindepth, attr, maxdepth, 
                   attr, whereclause, 
                   attr, dist_order)
            
            curs.execute(sql)
            stationData = curs.fetchall()

        elif (depthindex == 'min'):
            sql = """
            select distinct stations.lat,stations.long,stations.time,stations.station, min.minvalue::numeric, stations.s_id, %s.depthid %s
            from 
            stations, 
            %s, 
            (select distinct s_id, station, min(%s.value) as minvalue from %s where %s.depthid >= %s and %s.depthid <= %s group by s_id, station) min
            where 
            stations.s_id=%s.s_id 
            and %s.s_id = min.s_id
            and stations.station = %s.station
            and stations.station = min.station
            and stations.real_time >= '%s' and stations.real_time <= '%s'
            and %s.depthid >= %s and %s.depthid <= %s
            and %s.value = min.minvalue %s
            group by stations.lat,stations.long,stations.time,stations.station,min.minvalue,stations.s_id, %s.depthid %s
            """ % (attr, dist_query, 
                   attr, 
                   attr, attr, attr, mindepth, attr, maxdepth,  
                   attr, 
                   attr, 
                   attr, 
                   startTime, endTime, 
                   attr, mindepth, attr, maxdepth, 
                   attr, whereclause, 
                   attr, dist_order)
            curs.execute(sql)
            stationData = curs.fetchall()
        
        elif (depthindex == 'mean'):
            sql = """
            select distinct stations.lat,stations.long,stations.time,stations.station, mean.meanvalue::numeric, stations.s_id, mean.depth %s
            from 
            stations, 
            (select distinct s_id, station, avg(%s.value) as meanvalue, min(%s.depthid) as depth from %s where %s.depthid >= %s and %s.depthid <= %s group by s_id, station) mean
            where 
            mean.meanvalue <> 99
            and stations.station = mean.station
            and stations.real_time >= '%s' and stations.real_time <= '%s'
            group by stations.lat,stations.long,stations.time,stations.station,mean.meanvalue,stations.s_id, mean.depth %s
            """ % (dist_query, 
                   attr, attr, attr, attr, mindepth, attr, maxdepth,  
                   startTime, endTime, 
                   dist_order)
            curs.execute(sql)
            stationData = curs.fetchall()
            
#            and %s.value = mean.meanvalue %s

        else:
            #GET RECORDS FOR SPECIFIED DEPTH (USING MINDEPTH):
            if mode == 'normal':
                sql = """
                select distinct stations.lat,stations.long,stations.time,stations.station,%s.value::numeric,stations.s_id,%s.depth %s
                from stations, %s where stations.s_id=%s.s_id and %s.depthid = %s and stations.station = %s.station and %s.value is not null and %s.depth is not null
                and stations.real_time >= '%s' and stations.real_time <= '%s' %s""" % (attr, attr, dist_query, attr, attr, attr, mindepth, attr, attr, attr, startTime, endTime, whereclause)
                curs.execute(sql);
                stationData = curs.fetchall()

            #GET 2D SURFACE FOR SPECIFIED DEPTH (USING MINDEPTH):
            if mode == 'surface':
                stationData = []
                whereclause = whereclause.replace("%20"," ")
                sql = """
                select distinct stations.lat,stations.long,stations.time,stations.station,%s.value::numeric,stations.s_id,%s.depth
                from stations, %s where stations.s_id=%s.s_id and %s.depthid = %s and stations.station = %s.station and %s.value is not null and %s.depth is not null
                and stations.real_time >= '%s' and stations.real_time <= '%s' %s""" % (attr, attr, attr, attr, attr, mindepth, attr, attr, attr, startTime.replace("%20"," "), endTime.replace("%20"," "), whereclause)
                curs.execute(sql)
                stationData = curs.fetchall()
            
                if len(stationData) > 2:
                    response = plot_hprofile(stationData, mode, attr, whereclause, lonmax, lonmin, latmax, latmin, mapwidth, mapheight, style, zmin, zmax)
                else:
                    response = "query returned 0."
    
    except Exception, Err:
        stationData.append("Sorry, Cannot return stations. depthindex: "+depthindex+ " | Error: " + str(Err) + "SQL: " + sql)
        return HttpResponse(str(stationData))
    finally:
        curs.close()
        pgconn.close()
        if mode == 'surface':
            if type(response) == str:
                return HttpResponse(response)
            else:
                return response
        else:
            return HttpResponse(str(stationData))

def plot_hprofile(mydata=[],ptype="surface",attr="components",whereclause="",lonmax="",lonmin="",latmax="",latmin="", mapwidth="", mapheight="", style="", zmin="", zmax=""): 
    try:
        zlist = []
        lat = []
        lon = []
        dpi = 150
        
        if len(mydata) == 0:
            return "Returned 0 record."
        else:
            pass

        ddata = {}
        
        try:
            for i in mydata:
                if i[0] <> None and i[1] <> None and i[4] <> None:
                    zlist.append(i[4]) #4 value
                    lat.append(i[0])
                    lon.append(i[1])
                else:
                    continue
        except Exception, e:
            return "Failed at data collection: " + str(e)
        
        try:
            #===================================================================
            # Store map extent variables
            #===================================================================
            ddata["ext_min_lat"] = float(latmin)
            ddata["ext_max_lat"] = float(latmax)
            ddata["ext_min_lon"] = float(lonmin)
            ddata["ext_max_lon"] = float(lonmax)
            
            #===================================================================
            # Generate figure
            #===================================================================
            fig = plt.figure(dpi=dpi, facecolor=None, edgecolor=None)
            fig.set_alpha(0.0)
            fig.set_figheight(float(mapheight)/dpi)
            fig.set_figwidth(float(mapwidth)/dpi)
            
            projection="merc"
            m = Basemap(llcrnrlon=ddata["ext_min_lon"], llcrnrlat=ddata["ext_min_lat"],
                        urcrnrlon=ddata["ext_max_lon"], urcrnrlat=ddata["ext_max_lat"], projection=projection,
                        lat_ts = 0.0,
                        )
            
            #===================================================================
            # Draw extra info (debug)
            #===================================================================
#            m.drawcoastlines(linewidth=0.5)
#            m.drawcountries(linewidth=0.5)

        except Exception, e:
            plt.close('all')
            return "Failed at figure set up: " + str(e)
        
        if ptype == "surface":
            try:
                x = np.linspace(ddata["ext_min_lon"], ddata["ext_max_lon"],700)
                y = np.linspace(ddata["ext_min_lat"], ddata["ext_max_lat"],700)
            except Exception, e:
                plt.close('all')
                return "Failed at np.linspace: " + str(e)
            
            #===================================================================
            # Triangulate data
            #===================================================================
            try:
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    
                    xi, yi = np.meshgrid(x,y)
                    znew = griddata(lon,lat,zlist,xi,yi,interp='nn')

#                    tri = delaunay.Triangulation(lon,lat)
#                    interp = tri.nn_interpolator(zlist)
#                    znew = interp(xi,yi)

                    ## GET MIN/MAX VALUE AFTER INTERPOLATION
#                    zmin = znew[np.where(np.isnan(znew) == False)].min()
#                    zmax = znew[np.where(np.isnan(znew) == False)].max()                        
                    
            except Exception, e:
                plt.close('all')
                return "Failed at Triangulation: " + str(e)

            # subplot
            try:
                plt.subplot(111)
                plt.rcParams['font.size'] = 7
                plt.rcParams["text.usetex"]
                lon, lat = m(lon,lat)             
                xi, yi = m(xi, yi)
                
                #===============================================================
                # Scatter plot
                #===============================================================
#                m.scatter(lon,lat,zlist, marker='o', c='y', alpha=0.25)
                                
                #===============================================================
                # Get color map:
                # http://matplotlib.sourceforge.net/examples/pylab_examples/show_colormaps.html
                #===============================================================
                
                ax = plt.gca()
                #===============================================================
                # Transparency
                #===============================================================
                fig.patch.set_alpha(0.0)
                
                #===============================================================
                # Use basemap coodinates to plot interpolated image, contours and 
                # contour labels.
                #===============================================================
                # Set data extent
                ext = (ddata["ext_min_lon"], ddata["ext_max_lon"],ddata["ext_min_lat"], ddata["ext_max_lat"])
#                im = plt.pcolor(xi, yi, znew)

                if zmin <> None:
                    zmin = float(zmin)
                    zmax = float(zmax)
                im = m.imshow(znew, extent=ext, cmap=cm.get_cmap(style), origin='lower', interpolation='nearest', vmin=zmin, vmax=zmax)#, extent=ext)
                c = m.contour(xi, yi, znew, extent=ext) #, colors="w"
                l = plt.clabel(c, inline=1, fontsize=4)
                                
                cb = plt.colorbar(im, orientation='horizontal',shrink=0.2)#,spacing='proportional',extend='max')
                cb.set_label(attr)
                l,b,w,h = plt.gca().get_position().bounds
                ll,bb,ww,hh = cb.ax.get_position().bounds
                cb.ax.set_position([ll+.4, bb-.15, ww, hh])

                #===============================================================
                # Use basemap coordinates to set x/y limit
                #===============================================================
                lonmax, latmax = m(ddata["ext_max_lon"], ddata["ext_max_lat"])
                lonmin, latmin = m(ddata["ext_min_lon"], ddata["ext_min_lat"])
                ax.set_xlim(lonmin, lonmax)
                ax.set_ylim(latmin, latmax)
                
                #===============================================================
                # Remove frames and axis
                #===============================================================
                ax.set_frame_on(False)
                ax.set_clip_on(False)
                ax.set_position([0,0,1,1])            
                plt.axis('off')                

            except Exception, e:
                plt.close('all')
                return "Failed at imshow: " + str(e)
                
            try:
                #===============================================================
                # Return response
                #===============================================================
                canvas = FigureCanvasAgg(fig)
                response = HttpResponse(content_type='image/png')
                canvas.print_png(response)
                return response
            
            except Exception, e:
                plt.close('all')
                return "Failed at response: " + str(e)
    except Exception, e:
        return str(e)
    
def plot_vprofile(mydata=[],ptype="2dvquery",attr="components", style='jet', interp='linear'):
    try:
#        errormsg = "http://dwh.asascience.com:8080/ctd_download/vprofile/no_image_404.png"

        xlist = []
        ylist = []
        zlist = []
        lat = []
        lon = []

        if len(mydata) == 0:
            return "Data not found."
        else:
            pass
        
        cnt = 0
        ddata = {}
        conv = 111120
        
        for i in mydata:
            cnt+=1
            if i[7] <> None and i[6] <> None and i[4] <> None:
                lat.append(i[0])        #0 lat
                lon.append(i[1])        #1 lon
                zlist.append(i[4])      #4 value
                ylist.append(i[6])      #2 depth
                xlist.append(i[7]*conv) #3 distance  
            else:
                continue

        if len(zlist) == 0:
            return "no data returned."

        try:
            ddata["min_lat"] = array(lat).min()
            ddata["max_lat"] = array(lat).max()
            ddata["min_lon"] = array(lon).min()
            ddata["max_lon"] = array(lon).max()
            ddata["mindist"] = array(xlist).min()
            ddata["maxdist"] = array(xlist).max()
            ddata["mindepth"] = array(ylist).min()
            ddata["maxdepth"] = array(ylist).max()
##                ddata["minval"] = array(zlist).min()
##                ddata["maxval"] = array(zlist).max()
        except Exception, e:
            plt.close('all')
            et, ev, tb = sys.exc_info()
            lineno = " - Error Line #: " + str(traceback.tb_lineno(tb))
            return "np.array error: " + str(e) + ": " + lineno
        
        fig = plt.figure(num=None, figsize=(9, 9), dpi=70, facecolor='w', edgecolor='k')
        plt.rcParams['font.size'] = 10

        #=======================================================================
        # 3D Scatter Plot
        #=======================================================================
        if ptype == "3dvquery":
            ax = fig.gca(projection='3d')
            ax.scatter(xlist, ylist, zlist, c='r', marker='o')
            ax.set_xlabel('Distance')
            ax.set_ylabel('Depth')
            ax.set_zlabel('Value')

        #=======================================================================
        # 2D Vertical Profile Plot
        #=======================================================================
        if ptype == "2dvquery":
            try:
                x = np.linspace(ddata["mindist"], ddata["maxdist"])
                y = np.linspace(ddata["mindepth"], ddata["maxdepth"])
            except Exception, e:
                plt.close('all')
                et, ev, tb = sys.exc_info()
                lineno = " - Error Line #: " + str(traceback.tb_lineno(tb))
                return "np.linespace error: " + str(e) + ": " + lineno
            

            try:
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    xi, yi = np.meshgrid(x,y)
                    
                    if interp == 'nearest_neighbor':
                        #Using Matplotlib Delaunay Tringualtion linear interpolation method
                        tri = delaunay.Triangulation(xlist,ylist)
                        do_interp = tri.nn_interpolator(zlist)
                        znew = do_interp(xi,yi)
                    
                    elif interp == 'cubic':
                        #Using SciPy.Interpolate Griddata cubic interpolation method
                        znew = interpolate.griddata((xlist, ylist), zlist, (xi, yi), method='cubic')
                    
                    #----------------------------------------------------------------------
                    #not working
                    #elif interp == 'spline':
                    #    #Using SciPy.Interpolate spline interpolation method
                    #    tck = interpolate.bisplrep(xlist, ylist, zlist, s=0)
                    #    znew = interpolate.bisplev(xi, yi, tck)
                    
                    #not working (grids to large)
                    #elif interp == 'radial':
                    #    #Using SciPy.Interpolate radial interpolation method - MAY NOT BE A GOOD IDEA
                    #    rbf = interpolate.Rbf(xlist, ylist, zlist, function='inverse multiquadric')
                    #    znew = rbf(xi, yi)
                    #----------------------------------------------------------------------             
                    
                    
                    # use linear by defualt or if something incorrect is passed.
                    else:
                        #Using SciPy.Interpolate Griddata linear interpolation method
                        znew = interpolate.griddata((xlist, ylist), zlist, (xi, yi), method='linear')
                             

                    
            except Exception, e:
                plt.close('all')
                et, ev, tb = sys.exc_info()
                lineno = " - Error Line #: " + str(traceback.tb_lineno(tb))
                return "Failed at Interpolation: %s (X=%d,Y=%d,Z=%d) %s" % (str(e),len(xlist),len(ylist),len(zlist), lineno)

            
            #===================================================================
            # Subplot
            #===================================================================
            try:
                # set data extent
                extent = (ddata["mindist"], ddata["maxdist"],ddata["mindepth"], ddata["maxdepth"])
                
                plt.subplot(111)
                plt.xlim([ddata["mindist"], ddata["maxdist"]])
                plt.ylim([ddata["mindepth"], ddata["maxdepth"]])
                
                #JF 6/8/12 - making the scatter plot points always one size, in some cases they can be huge...
                #plt.scatter(xlist,ylist,zlist, marker='o', c='y', alpha=0.25)
                plt.scatter(xlist,ylist,s=5, marker='o', c='y', alpha=0.25)
                
                plt.contour(znew, origin='lower', extent=extent)
                                
                ##JF 6/7/12 - Changing interpolation method on final plot also, to Gaussian (smoother looking output)
                ##plt.imshow(znew, cmap=cm.get_cmap(style), extent=extent, origin='lower', interpolation='nearest')
                plt.imshow(znew, cmap=cm.get_cmap(style), extent=extent, origin='lower', interpolation='gaussian')
                
                # figure design
                title = "Vertical Profile \nstart: x="+str(ddata["min_lon"])+" y="+str(ddata["min_lat"]) + " end: x="+str(ddata["max_lon"])+" y="+str(ddata["max_lat"]) + " " + attr + "\n" + "Points used: " + str(len(mydata))
                plt.title(title)
                plt.axis('tight')
                plt.xlabel('Distance (m)')
                plt.ylabel('Depth (m)')
                plt.axis([float(ddata["mindist"]), float(ddata["maxdist"]),float(ddata["maxdepth"]),float(ddata["mindepth"])])  # Flips depth (y)
                plt.colorbar()
            except Exception, e:
                plt.close('all')
                return "Failed at Plotting: " + str(e)

        #=======================================================================
        # Output file
        #=======================================================================
        try:
            #return "TEST4: " + getpass.getuser() + ','.join(dir(matplotlib))
            today = datetime.now()
            dataDir = r"C:\\Program Files (x86)\Apache Software Foundation\Apache2.2\htdocs\ctd_download\vprofile"
            #filename = "ctd_vprofile_"+attr+"_"+today.strftime("%Y%m%d%H%M%S")+".png"
            filename = "ctd_vprofile_"+attr+"_"+interp+"_"+today.strftime("%Y%m%d%H%M%S")+".png"
            filepath = os.path.join(dataDir,filename)
            fig.savefig(filepath, dpi=65)
            plt.close('all')
            
            ##Chainge loncation for testing.
            result = "http://dwh.asascience.com:8080/ctd_download/vprofile/" + filename
            #result = "http://agsdev01:8081/ctd_download/vprofile/" + filename
            return result
        
        except Exception, e:
            plt.close('all')
            return "Failed at plot export: " + str(e)
        
    
    except Exception, e:
        et, ev, tb = sys.exc_info()
        top = traceback.extract_stack()[-1]
        filename = ", ".join([type(e).__name__, os.path.basename(top[0]), str(top[1])])
        lineno = " - Error Line # = " + str(traceback.tb_lineno(tb)) 
        result = str(e) + " - " + filename + lineno
        plt.close('all')
        return result
     

