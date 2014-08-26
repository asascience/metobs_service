# Create your views here.
#from django.template import Context, loader
from django.shortcuts import render_to_response, get_object_or_404
#from ctd_j.models import *
from django.http import HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.core.urlresolvers import reverse

import random, string, os, sys
#import bpgsql as pgs
from datetime import datetime

import psycopg2 as pgs

#json as response
#from django.utils import simplejson as json
import json
from django.core.serializers.json import DjangoJSONEncoder
#from djgeojson.serializers import Serializer as GeoJSONSerializer
import ordereddict 
import traceback, os.path

# import matplotlib
# from matplotlib import cm
# matplotlib.use('Agg')
# import mpl_toolkits.mplot3d.axes3d
# import matplotlib.pyplot as plt
# from matplotlib import delaunay
# from matplotlib.mlab import griddata
# # scipy griddata
# from scipy import interpolate
# from matplotlib.backends.backend_agg import FigureCanvasAgg
# from mpl_toolkits.basemap import Basemap
# import numpy as np
# from numpy import array
# import subprocess
# from PIL import Image
# import re
#import getpass


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
# Request stations and return lat,long, time and station_names
# default to all available dates and data
#===============================================================================
def getstations(request):
    attr = request.GET['attr']
    #depthindex = request.GET['depthindex']
    #startTime = request.GET['startTime']
    #endTime = request.GET['endTime']
    mode = request.GET['mode']
    whereclause = request.GET['y']
    
    # try:
    #     bbox = request.GET['BBOX']  
    #     bbox = bbox.split(',')      
    # except:
    #     bbox = ""

    # if bbox == "":
    #     bbox =",,,"
    #     bbox = bbox.split(',')  
    #     lonmin = bbox[0]
    #     latmin = bbox[1]
    #     lonmax = bbox[2]
    #     latmax = bbox[3]
    
    #===========================================================================
    # DB Connection.
    #===========================================================================
    try:
        pgconn = pgs.connect(user="postgres",password="PinkPanther#3",host="localhost",port='5432',dbname="oceansmap_obs")
        curs = pgconn.cursor()
    except:
        return HttpResponse("Sorry, Cannot Connect to Data.")
        

    stationData = []
    #just anadarko now
    clientID = 1;
    
    curs.execute("select station_id, station_name, string_name_id, lat_loc, lon_loc, start_date, end_date, station_desc from data.stations where client_id="+str(clientID)+" order by station_name;")
    
    rows_serial = json.dumps(curs.fetchall(), cls=DjangoJSONEncoder);
    rows_json = json.loads(rows_serial)

    objects_geojson = []
    collection_list = ordereddict.OrderedDict()
    for row in rows_json:
        d = ordereddict.OrderedDict()
        d['id'] = row[0]
        d['type']= 'Feature'
        p = ordereddict.OrderedDict()
        p['mooringname'] = row[1]
        p['station_name'] = row[2]
        p['start'] = row[5]
        p['end'] = row[6]
        p['desc'] = row[7]
        d['properties'] = p;
        g= ordereddict.OrderedDict()
        g['type'] = 'Point'
        g['coordinates'] = [row[4],row[3]]
        d['geometry']=g;
        objects_geojson.append(d)
    
    collection_list['type']= "FeatureCollection";
    collection_list['features'] =objects_geojson;
    stationData = json.dumps(collection_list)

    try:            
        if(attr == 'and'):
            clientID = 1;
            #curs.execute("select station_id,station_name as mooringname, string_name_id as stationname,lon_loc,lat_loc,start_date,end_date,station_desc from data.stations where client_id="+str(clientID)+" order by mooringname;")
            #stationData = GeoJSONSerializer().serialize(curs.fetchall(), use_natural_keys=True);
            #stationData = json.dumps(curs.fetchall(), cls=DjangoJSONEncoder);

    
    except Exception, Err:
        stationData.append("Sorry, Cannot return sdf. ")
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


