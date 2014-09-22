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
    
    try:            
        if(attr == 'and'):
            #just anadarko now
            clientID = 1;
            
            curs.execute("select station_id, station_name, string_name_id, lat_loc, lon_loc, start_date, end_date, station_desc,deployment_id,params,main_depth,pretty_params,depth_var from data.stations where start_date is not null and client_id="+str(clientID)+" order by station_name;")
            
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
                p['deploy'] = row[8]
                p['params'] = row[9]
                p['pretty_params'] = row[11]
                p['avedepth'] = row[10]
                p['depth_values'] = row[12]
                p['sid'] = row[0]
                d['properties'] = p;
                g= ordereddict.OrderedDict()
                g['type'] = 'Point'
                g['coordinates'] = [float(row[4]),float(row[3])]
                d['geometry']=g;
                objects_geojson.append(d)
            
            collection_list['type']= "FeatureCollection";
            collection_list['features'] =objects_geojson;
            stationData = json.dumps(collection_list)
        
        else:
            stationData = "No data for this client"

    
    except Exception, Err:
        stationData.append("Sorry, Cannot return stations. ")
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


#===============================================================================
# Request vertical profile for specific station and date
#===============================================================================
def getvertprofile(request):
    
    paramaterDic = {"current_speed":1,"current_direction":2,"atmospheric_pressure":3,"humidity":4,"rain":5,"air_temp":6,"wind_speed_10m_max":7,"wind_speed_1_5m_max":8,"wind_direction_10m":9,"wind_direction_1_5m":10,"wind_speed_10m_mean":11,"wind_speed_1_5m_mean":12,"vert_wind_speed_max":13,"vert_wind_speed_mean":14,"vert_wind_speed_min":15,"salinity":16,"sound_velocity":17,"density":18,"turbidity":19,"water_temp":20,"height":21,"voltage":22,"tide_height":23}

    attr = request.GET['attr']
    #depthindex = request.GET['depthindex']
    #mode = request.GET['z']
    #timerequest = request.GET['t']
    #paramrequest = paramaterDic.get(request.GET['p'])
    #whereclause = request.GET['y']
    
    
    #===========================================================================
    # DB Connection.
    #===========================================================================
    try:
        pgconn = pgs.connect(user="postgres",password="PinkPanther#3",host="localhost",port='5432',dbname="oceansmap_obs")
        curs = pgconn.cursor()
    except:
        return HttpResponse("Sorry, Cannot Connect to Data.")
        

    vertData = []
    
    try:            
        if(attr == 'and'):
            #just anadarko now
            clientID = 1;
            
            curs.execute("select station_id, station_name, string_name_id, lat_loc, lon_loc, start_date, end_date, station_desc,deployment_id,notes from data.stations where start_date is not null and client_id="+str(clientID)+" order by station_name;")
            
            rows_serial = json.dumps(curs.fetchall(), cls=DjangoJSONEncoder);
            rows_json = json.loads(rows_serial)

            # objects_geojson = []
            # collection_list = ordereddict.OrderedDict()
            # for row in rows_json:
            #     d = ordereddict.OrderedDict()
            #     d['id'] = row[0]
            #     d['type']= 'Feature'
            #     p = ordereddict.OrderedDict()
            #     p['mooringname'] = row[1]
            #     p['station_name'] = row[2]
            #     p['start'] = row[5]
            #     p['end'] = row[6]
            #     p['desc'] = row[7]
            #     p['deploy'] = row[8]
            #     p['params'] = row[9]
            #     d['properties'] = p;
            #     g= ordereddict.OrderedDict()
            #     g['type'] = 'Point'
            #     g['coordinates'] = [float(row[4]),float(row[3])]
            #     d['geometry']=g;
            #     objects_geojson.append(d)
            
            collection_list['type']= "FeatureCollection";
            collection_list['features'] = objects_geojson;
            vertData = json.dumps(collection_list)
        
        else:
            vertData = "No data for this client"
    
    except Exception, Err:
        vertData.append("Sorry, Cannot return stations. ")
        return HttpResponse(str(vertData))
    finally:
        curs.close()
        pgconn.close()
        if mode == 'surface':
            if type(response) == str:
                return HttpResponse(response)
            else:
                return response
        else:
            return HttpResponse(str(vertData))


#===============================================================================
# Request time series for start and end date profile
#===============================================================================
def gettimeseries(request):
    ##sensor dictionary
    paramaterDic = {'current_speed':['m/s',1,'Water Speed'],'current_direction':['degrees from north',2,'Water Direction'],'atmospheric_pressure':['mBar',3,'Mean Atmospheric Pressure'],'humidity':['%',4,'Mean Humidity'],'rain':['mm',5,'Rain Amount'],'air_temp':['C',6,'Mean Air Temperature'],'wind_speed_10m_max':['m/s',7,'Maximum 10m Wind Speed'],'wind_speed_1_5m_max':['m/s',8,'Maximum 1.5m Wind Speed'],'wind_direction_10m':['TN',9,'Mean 10m Wind Direction'],'wind_direction_1_5m':['TN',10,'Mean 1.5m Wind Direction'],'wind_speed_10m_mean':['m/s',11,'Mean 10m Wind Speed'],'wind_speed_1_5m_mean':['m/s',12,'Mean 1.5m Wind Speed'],'vert_wind_speed_max':['m/s',13,'Maximum Vertical Wind Speed'],'vert_wind_speed_mean':['m/s',14,'Mean Vertical Wind Speed'],'vert_wind_speed_min':['m/s',15,'Minimum Vertical Wind Speed'],'salinity':['psu',16,'Water Salinity'],'sound_velocity':['m/s',17,'Sound Velocity'],'density':['kg/m3',18,'Density'],'turbidity':['NTU',19,'Turbidity'],'water_temp':['C',20,'Mean Water Temperature'],'height':['m',21,'Height'],'voltage':['V',22,'Voltage from Tide'],'tide_height':['m',23,'Tide Height'],'wave_height':['m',24,'Wave Height'],'wave_period':['seconds',25,'Wave Period'],'wave_direction':['d from north',26,'Wave Direction']}
    
    attr = request.GET['attr']
    #depthindex = request.GET['depthindex']
    stationID = request.GET['st']
    startTime = request.GET['starttime'].upper()
    endTime = request.GET['endtime'].upper()
    mode = request.GET['y']
    
    #check for multiple properties
    #this is to make the sql query look something like value1,value2,value3
    paramlist = str(request.GET['param']).split(',');
    param = '';
    realparamlist = [];
    if(len(paramlist)>0):
        for v in paramlist:
            if(paramaterDic.get(str(v).lower())):
                realparamlist.insert(len(realparamlist),v);
                param = param + ',value'+ str(paramaterDic.get(str(v).lower())[1]);
    else:
        if(paramaterDic.get(str(v).lower())):
            param = param +',value'+ str(paramaterDic.get(str(request.GET['param']).lower())[1]);
    
    #===========================================================================
    # DB Connection.
    #===========================================================================
    try:
        pgconn = pgs.connect(user="postgres",password="PinkPanther#3",host="localhost",port='5432',dbname="oceansmap_obs")
        curs = pgconn.cursor()
    except:
        return HttpResponse("Sorry, Cannot Connect to Data.")
        

    tsData = []
             
    try:
        if(param == ''):
            tsData = "Sorry, no parameters found.";

        elif(str(attr).lower() == 'and'):
            #just anadarko now
            clientID = 1;

            curs.execute("select collection_date, depth "+param+ " from data.data_values where station_id="+stationID+" and collection_date > '"+ startTime +"' and collection_date < '"+ endTime+ "';");
                            
            rows_serial = json.dumps(curs.fetchall(), cls=DjangoJSONEncoder);
            rows_json = json.loads(rows_serial)
            
            if(len(rows_json)>1):
                #this is to format json based on the number of parameters
                if(len(realparamlist)>1):
                    numP = 0;
                    collection_list = ordereddict.OrderedDict();
                    profile = ordereddict.OrderedDict();
                    profile['id'] = stationID;

                    for a in realparamlist:
                        objects_output = [];

                        for row in rows_json:            
                            g= ordereddict.OrderedDict();
                            g['time'] = row[0];
                            g['depth'] = row[1];

                            if(row[numP+2] is None):
                                continue
                            elif(row[numP+2] == -999):
                                continue
                            elif(row[numP+2] == -9999):
                                continue
                                #g['value'] = None
                            else:
                                g['value'] = float(row[numP+2])
                            
                            #shrink in up a bit
                            #d = ordereddict.OrderedDict()
                            #g['depth'] = row[1]
                            #d['result']=g;
                            objects_output.append(g)
                        
                        profileblock = ordereddict.OrderedDict();
                        profileblock['parametername'] = paramaterDic.get(str(a).lower())[2]
                        profileblock['parameterunits'] = paramaterDic.get(str(a).lower())[0]
                        profileblock['data'] = objects_output
                        
                        profile[a] =profileblock;
                        numP = numP+1;
                    
                    collection_list['profile']= profile;
                    tsData = json.dumps(collection_list)

                else:
                    objects_output = []
                    numP = 0;
                    collection_list = ordereddict.OrderedDict()
                    profile = ordereddict.OrderedDict()
                    profile['id'] = stationID

                    for row in rows_json:            
                        g= ordereddict.OrderedDict()
                        g['time'] = row[0]
                        g['depth'] = row[1]
                        if(row[numP+2] is None):
                            continue
                            #g['value'] = None
                        elif(row[numP+2] == -999):
                            continue
                        elif(row[numP+2] == -9999):
                            continue
                            
                        else:
                            g['value'] = float(row[2])
                        
                        #shrink in up a bit
                        #d = ordereddict.OrderedDict()
                        #g['depth'] = row[1]
                        #d['result']=g;
                        objects_output.append(g)
                    
                    profileblock=ordereddict.OrderedDict();
                    profileblock['parametername']= paramaterDic.get(str(request.GET['param']).lower())[2]
                    profileblock['parameterunits']= paramaterDic.get(str(request.GET['param']).lower())[0]
                    profileblock['data'] = objects_output
                    
                    profile[request.GET['param']] =profileblock;
                    collection_list['profile']= profile;
                    tsData = json.dumps(collection_list)
            
        else:
            tsData = "No data for this client"
    
    except Exception, Err:
        tsData = "Sorry, Cannot return time series. ";
        return HttpResponse(str(tsData))
    finally:
        curs.close()
        pgconn.close()
        if mode == 'surface':
            if type(response) == str:
                return HttpResponse(response)
            else:
                return response
        else:
            return HttpResponse(str(tsData))


#===============================================================================
# Request time series for start and end date profile
#===============================================================================
def value(request):
    ##sensor dictionary
    paramaterDic = {'current_speed':['m/s',1,'Water Speed'],'current_direction':['degrees from north',2,'Water Direction'],'atmospheric_pressure':['mBar',3,'Mean Atmospheric Pressure'],'humidity':['%',4,'Mean Humidity'],'rain':['mm',5,'Rain Amount'],'air_temp':['C',6,'Mean Air Temperature'],'wind_speed_10m_max':['m/s',7,'Maximum 10m Wind Speed'],'wind_speed_1_5m_max':['m/s',8,'Maximum 1.5m Wind Speed'],'wind_direction_10m':['TN',9,'Mean 10m Wind Direction'],'wind_direction_1_5m':['TN',10,'Mean 1.5m Wind Direction'],'wind_speed_10m_mean':['m/s',11,'Mean 10m Wind Speed'],'wind_speed_1_5m_mean':['m/s',12,'Mean 1.5m Wind Speed'],'vert_wind_speed_max':['m/s',13,'Maximum Vertical Wind Speed'],'vert_wind_speed_mean':['m/s',14,'Mean Vertical Wind Speed'],'vert_wind_speed_min':['m/s',15,'Minimum Vertical Wind Speed'],'salinity':['psu',16,'Water Salinity'],'sound_velocity':['m/s',17,'Sound Velocity'],'density':['kg/m3',18,'Density'],'turbidity':['NTU',19,'Turbidity'],'water_temp':['C',20,'Mean Water Temperature'],'height':['m',21,'Height'],'voltage':['V',22,'Voltage from Tide'],'tide_height':['m',23,'Tide Height'],'wave_height':['m',24,'Wave Height'],'Wave_period':['seconds',25,'Wave Period'],'wave_direction':['d from north',26,'Wave Direction']}
    
    attr = request.GET['attr']
    #depthindex = request.GET['depthindex']
    stationID = request.GET['st']
    startTime = request.GET['nowtime'].upper()
    mode = request.GET['y']
    
    #check for multiple properties
    #this is to make the sql query look something like value1,value2,value3
    paramlist = str(request.GET['param']).split(',');
    param = '';
    realparamlist = [];
    if(len(paramlist)>0):
        for v in paramlist:
            if(paramaterDic.get(str(v).lower())):
                realparamlist.insert(len(realparamlist),v);
                param = param + ',value'+ str(paramaterDic.get(str(v).lower())[1]);
    else:
        if(paramaterDic.get(str(v).lower())):
            param = param +',value'+ str(paramaterDic.get(str(request.GET['param']).lower())[1]);
    
    #===========================================================================
    # DB Connection.
    #===========================================================================
    try:
        pgconn = pgs.connect(user="postgres",password="PinkPanther#3",host="localhost",port='5432',dbname="oceansmap_obs")
        curs = pgconn.cursor()
    except:
        return HttpResponse("Sorry, Cannot Connect to Data.")
        
    
    tsData = []
    
    curs.execute("select collection_date, depth "+param+ " from data.data_values where station_id="+stationID+" and collection_date > '"+ startTime +"' and collection_date < '"+ endTime+ "';");
            
    rows_serial = json.dumps(curs.fetchall(), cls=DjangoJSONEncoder);
    rows_json = json.loads(rows_serial)
    
    #this is to format json based on the number of parameters
    if(len(realparamlist)>1):
        numP = 0;
        collection_list = ordereddict.OrderedDict();
        profile = ordereddict.OrderedDict();
        profile['id'] = stationID;
        
        for a in realparamlist:
            objects_output = [];

            for row in rows_json:            
                g= ordereddict.OrderedDict();
                g['time'] = row[0];

                if(row[numP+2] == None):
                    g['value'] = None
                else:
                    g['value'] = float(row[numP+2])
                
                #shrink in up a bit
                #d = ordereddict.OrderedDict()
                #g['depth'] = row[1]
                #d['result']=g;
                objects_output.append(g)
            
            profileblock = ordereddict.OrderedDict();
            profileblock['parametername'] = paramaterDic.get(str(a).lower())[2]
            profileblock['parameterunits'] = paramaterDic.get(str(a).lower())[0]
            profileblock['data'] = objects_output
            
            profile[a] =profileblock;
            numP = numP+1;
        
        collection_list['profile']= profile;
        tsData = json.dumps(collection_list)

    else:
        objects_output = []
        collection_list = ordereddict.OrderedDict()
        profile = ordereddict.OrderedDict()
        profile['id'] = stationID

        for row in rows_json:            
            g= ordereddict.OrderedDict()
            g['time'] = row[0]
            if(row[2] == None):
                g['value'] = None
            else:
                g['value'] = float(row[2])
            
            #shrink in up a bit
            #d = ordereddict.OrderedDict()
            #g['depth'] = row[1]
            #d['result']=g;
            objects_output.append(g)
        
        profileblock=ordereddict.OrderedDict();
        profileblock['parametername']= paramaterDic.get(str(request.GET['param']).lower())[2]
        profileblock['parameterunits']= paramaterDic.get(str(request.GET['param']).lower())[0]
        profileblock['data'] = objects_output
        
        profile[request.GET['param']] =profileblock;
        collection_list['profile']= profile;
        tsData = json.dumps(collection_list)
   
    try:
        if(param == ''):
            tsData = "Sorry, no parameters found.";

        elif(str(attr).lower() == 'and'):
            #just anadarko now
            clientID = 1;
            

        
        else:
            tsData = "No data for this client"
    
    except Exception, Err:
        tsData = "Sorry, Cannot return time series. ";
        return HttpResponse(str(tsData))
    finally:
        curs.close()
        pgconn.close()
        if mode == 'surface':
            if type(response) == str:
                return HttpResponse(response)
            else:
                return response
        else:
            return HttpResponse(str(tsData))

