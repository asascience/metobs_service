# Create your views here.
#from django.template import Context, loader
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.db import connections 

import string, os, sys
#import bpgsql as pgs random, 
from datetime import datetime
#import psycopg2 as pgs

#json as response
#from django.utils import simplejson as json
import json
from django.core.serializers.json import DjangoJSONEncoder
#from djgeojson.serializers import Serializer as GeoJSONSerializer
import ordereddict 
import traceback, os.path

from cStringIO import StringIO

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
        #pgconn = pgs.connect(user="postgres",password="PinkPanther#3",host="localhost",port='5432',dbname="oceansmap_obs")
        #curs = pgconn.cursor()
        curs = connections['default'].cursor()
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
            curs.close()
            #pgconn.close()
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
        curs.close()
        #pgconn.close()
        stationData.append("Sorry, Cannot return stations. ")
        return HttpResponse(str(stationData))
    finally:
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
    attr = request.GET['attr']
    timerequest = request.GET['t']
    stationID = request.GET['st']
    #depthindex = request.GET['depthindex']
    mode = request.GET['y']
    #paramrequest = paramaterDic.get(request.GET['p'])
    #whereclause = request.GET['y']
    
    #===========================================================================
    # DB Connection.
    #===========================================================================
    try:
        #pgconn = pgs.connect(user="postgres",password="PinkPanther#3",host="localhost",port='5432',dbname="oceansmap_obs")
        #curs = pgconn.cursor()
        curs = connections['default'].cursor()
    except:
        return HttpResponse("Sorry, Cannot Connect to Data.")
        
    vertData = []

    try:            
        if(attr == 'and'):
            #just anadarko now
            clientID = 1;
            
            curs.execute("select DISTINCT ON (depth) depth ,value1, value2 from data.data_values where collection_date = '"+timerequest+"' and station_id = "+stationID+" and value1 is not null;");
            
            rows_serial = json.dumps(curs.fetchall(), cls=DjangoJSONEncoder);
            rows_json = json.loads(rows_serial)
            curs.close()
            #pgconn.close()
            if(len(rows_json)>1):         
                collection_list = ordereddict.OrderedDict();
                profile = ordereddict.OrderedDict();
                profile['id'] = stationID;

                speedDict = ordereddict.OrderedDict();
                directionDict = ordereddict.OrderedDict();

                objects_speed =  []
                objects_direction = [];

                for row in rows_json:            
                    
                    if(row[1] == -999):
                        continue
                    elif(row[1] == -9999):
                        continue
                        #g['value'] = None
                    else:
                        sp = [float(row[1]), float(row[0])*-1];
                        dt = [float(row[2]), float(row[0])*-1];
                    
                    objects_direction.append(dt)
                    objects_speed.append(sp)
                

                speedDict['x_label'] = "Current Speed cm/s";
                speedDict['y_label'] = "Depth (m)";
                speedDict['data'] = objects_speed;
                speedDict['time'] = timerequest;
                directionDict['x_label'] = "Current Direction d North";
                directionDict['y_label'] = "Depth (m)";
                directionDict['time'] = timerequest;
                directionDict['data'] = objects_direction;

                profile['speed'] = speedDict;
                profile['direction'] = directionDict;

                # temp to copy the EHI stuff
                statusinfo = ordereddict.OrderedDict();
                statusinfo['message'] = 'fine'
                statusinfo['status_code'] = 'Critical'
                statusinfo['status'] = 2;

                collection_list['profile']= profile;
                collection_list['status_info']= statusinfo;
                vertData = json.dumps(collection_list);
     
        else:
            vertData = "No data for this client"
    
    except Exception, Err:
        curs.close()
        #pgconn.close()
        vertData.append("Sorry, Cannot return Values. ")
        return HttpResponse(str(vertData))
    finally:
        if mode == 'surface':
            if type(response) == str:
                return HttpResponse(response)
            else:
                return response
        else:
            return HttpResponse(str(vertData))


#===============================================================================
# Request time series for start and end date profile
#http://localhost:8080/oceansmap65/metobs/gettimeseriescurrents/?attr=and&st=33&starttime=2011-12-22T00:00:00&endtime=2012-01-05T00:00:00&y=aasdff&d=3
#===============================================================================
def gettimeseriescurrents(request):

    ##sensor dictionary
    paramaterDic = {'current_speed':['cm/s',1,'Current Speed'],'current_direction':['degrees',2,'Current Direction'],'atmospheric_pressure':['mBar',3,'Mean Atmospheric Pressure'],'humidity':['%',4,'Mean Humidity'],'rain':['mm',5,'Rain Amount'],'air_temp':['C',6,'Air Temperature'],'wind_speed_10m_max':['m/s',7,'Maximum 10m Wind Speed'],'wind_speed_1_5m_max':['m/s',8,'Maximum 1.5m Wind Speed'],'wind_direction_10m':['TN',9,'Mean 10m Wind Direction'],'wind_direction_1_5m':['TN',10,'Mean 1.5m Wind Direction'],'wind_speed_10m_mean':['m/s',11,'Mean 10m Wind Speed'],'wind_speed_1_5m_mean':['m/s',12,'Mean 1.5m Wind Speed'],'vert_wind_speed_max':['m/s',13,'Maximum Vertical Wind Speed'],'vert_wind_speed_mean':['m/s',14,'Mean Vertical Wind Speed'],'vert_wind_speed_min':['m/s',15,'Minimum Vertical Wind Speed'],'salinity':['psu',16,'Water Salinity'],'sound_velocity':['m/s',17,'Sound Velocity'],'density':['kg/m3',18,'Density'],'turbidity':['NTU',19,'Turbidity'],'water_temp':['C',20,'Water Temperature'],'height':['m',21,'Surface Elevation'],'voltage':['V',22,'Voltage from Tide'],'tide_height':['m',23,'Tide Height'],'wave_height':['m',24,'Wave Height'],'wave_period':['seconds',25,'Wave Period'],'wave_direction':['degrees',26,'Wave Direction']}
    attr = request.GET['attr']
    #depthindex = request.GET['depthindex']
    stationID = request.GET['st']
    startTime = request.GET['starttime'].upper()
    endTime = request.GET['endtime'].upper()
    dpth = request.GET['d']
    mode = request.GET['y']
    
    #default to current speed and direction 
    realparamlist = ['current_speed','current_direction'];
    param = 'value1,value2';

    #===========================================================================
    # DB Connection.
    #===========================================================================
    try:
        #pgconn = pgs.connect(user="postgres",password="PinkPanther#3",host="localhost",port='5432',dbname="oceansmap_obs")
        #curs = pgconn.cursor()
        curs = connections['default'].cursor()
    except:
        return HttpResponse("Sorry, Cannot Connect to Data.")
        
    tsData = []
    curs.execute("select collection_date,  "+param+ " from data.data_values_1h where station_id="+stationID+" and collection_date > '"+ startTime +"' and collection_date < '"+ endTime+ "' and depth ="+dpth+";");
                            
    rows_serial = json.dumps(curs.fetchall(), cls=DjangoJSONEncoder);
    rows_json = json.loads(rows_serial)
    curs.close()
    #pgconn.close()
    
    try:
        if(param == ''):
            tsData = "Sorry, no parameters found.";

        elif(str(attr).lower() == 'and'):
            #just anadarko now
            clientID = 1;

            if(len(realparamlist)>1):
                numP = 0;
                collection_list = ordereddict.OrderedDict();
                profile = ordereddict.OrderedDict();
                profile['id'] = stationID;
                profile['depth'] = float(dpth);

                for a in realparamlist:
                    objects_output = [];

                    for row in rows_json:            
                        g= ordereddict.OrderedDict();
                        g['time'] = row[0];

                        if(row[numP+1] is None):
                            continue
                        elif(row[numP+1] == -999):
                            continue
                        elif(row[numP+1] == -9999):
                            continue
                            #g['value'] = None
                        else:
                            g['value'] = float(row[numP+1])
                        
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
            tsData = "No data for this client"
    
    except Exception, Err:
        curs.close()
        #pgconn.close()
        tsData = "Sorry, Cannot return time series. ";
        return HttpResponse(str(tsData));

    finally:
        if mode == 'surface':
            if type(response) == str:
                return HttpResponse(response)
            else:
                return response
        else:
            return HttpResponse(str(tsData))

#===============================================================================
# Request time series for start and end date profile
#http://localhost:8080/oceansmap65/metobs/gettimeseriescurrents/?attr=and&st=33&starttime=2011-12-22T00:00:00&endtime=2012-01-05T00:00:00&y=aasdff&d=3
#===============================================================================
def gettimeseriescurrentsimage(request):

    import numpy as np
    import matplotlib as mpl
    mpl.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.dates import date2num
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    import matplotlib.gridspec as gridspec
    from dateutil import parser
    np.seterr(divide='ignore', invalid='ignore')

    attr = request.GET['attr']
    stationID = request.GET['st']
    startTime = request.GET['starttime'].upper()
    endTime = request.GET['endtime'].upper()
    dpth = request.GET['d'].split(',');
    

    try:
        wd = request.GET['w']
        ht = request.GET['h']
        mode = request.GET['y']
        sampledata = request.GET['samp'];
        if wd == '':
            wd = 900
            ht = 500        
    except:
        wd = 900
        ht = 500  
        mode = 'surface'
        sampledata = 'true';
    
    #default to current speed and direction 
    param = 'value1,value2';

    #===========================================================================
    # DB Connection.
    #===========================================================================
    try:
        #pgconn = pgs.connect(user="postgres",password="PinkPanther#3",host="localhost",port='5432',dbname="oceansmap_obs")
        #curs = pgconn.cursor()
        curs = connections['default'].cursor()
    except:
        return HttpResponse("Sorry, Cannot Connect to Data.")
        
    #not used
    tsData = "Choose Surface"
    figsize=(10, 6), 
    fig = plt.figure(num=None, dpi=100)
    fig.set_alpha(0.0)
    fig.set_figheight(float(ht)/100)
    fig.set_figwidth(float(wd)/100)
    ax = fig.add_subplot(1,1,1)
    cmap = plt.cm.rainbow

    props = {'units' : "dots",
         'width' : 1,
         'headwidth': 0,
         'headlength': 0,
         'headaxislength': 0,
         'scale' : .7,
         'cmap': cmap
         }
    
    dpthtics = []

    #iterate through depths
    for d in dpth:

        if d == '':
            continue

        if(sampledata == 'true'):
            curs.execute("select collection_date,  "+param+ " from data.data_values_1h where station_id="+stationID+" and collection_date > '"+ startTime +"' and collection_date < '"+ endTime+ "' and depth ="+d+";");
        else:
            curs.execute("select collection_date,  "+param+ " from data.data_values where station_id="+stationID+" and collection_date > '"+ startTime +"' and collection_date < '"+ endTime+ "' and depth ="+d+";");
                
        rows_serial = json.dumps(curs.fetchall(), cls=DjangoJSONEncoder);
        rows_json = json.loads(rows_serial)
        
        clientID = 1;
        tarray = []
        dsarray = []

        if len(rows_json)<1:
            continue

        for row in rows_json:            
            
            if(row[1] is None):
                continue
            elif(row[1] == -999):
                continue
            elif(row[1] == -9999):
                continue
            else:
                #2012-01-21T00:30:00  ,"%Y-%B-%dT%H:%M:%S"
                tarray.append(parser.parse(row[0]))
                dsarray.append([row[1],row[2]])
        
        #this is to check for null or 999 data
        if (len(dsarray)>0):
            
            dpthtics.append(int(d)*-1)
            data = np.array(dsarray, dtype=np.float)
            
            speeds  = data[:,0]
            directions  = data[:,1]
            
            #times = range(len(speeds))
            label_scale = 10
            #unit_label = "%3g %s"%(label_scale, "cm/s")
            unit_label = "cm/s"
            
            y = (int(d)*-1)
            dir_rad = directions / 180. * np.pi
            u = np.sin(dir_rad) * speeds
            v = np.cos(dir_rad) * speeds

            C = np.sqrt(speeds**1)
            
            time, u, v = map(np.asanyarray, (tarray, u, v))

            Q = ax.quiver(date2num(time), y, u, v, C, **props)
            ax.quiverkey(Q, X=.9, Y=.9999, U=label_scale, label=unit_label, labelpos='S',coordinates='axes',fontproperties={'size': 'small'})

    curs.close()
    
    if (len(dpthtics)<1):
        mode = 'none'
        tsData = 'Please check your request'
    else:
        #set number of date ticks
        # xaxis = ax.xaxis
        # v = len(times)/(len(xaxis.get_major_ticks())-1)
        # #v = len(times)/len(xaxis.get_major_ticks())
        # tsShort = []
        # tsShortNum = []
        # for da in tarray[::v]:
        #     tsShort.append(str(da.month)+'-'+str(da.day)+'-'+str(da.hour)+'h')
        #     tsShortNum.append(da.day) 
        # xaxis.set_ticklabels(tsShort,rotation='45')
        plt.xticks(rotation=12)
        ax.xaxis_date()
        
        #buffer the chart vertical depth ticks
        yaxis = ax.yaxis
        maxi = (np.amax(np.array(dpthtics,dtype=np.int))+1)
        mini = (np.amin(np.array(dpthtics,dtype=np.int))-1)
        dpthtics.append(maxi)
        dpthtics.append(mini)
        yaxis.set_ticks(dpthtics)

        # legend
        ax1 = fig.add_axes([0.904, .31, 0.02, 0.377])
        norm = mpl.colors.Normalize(vmin=min(speeds), vmax=max(speeds))
        cb1 = mpl.colorbar.ColorbarBase(ax1, cmap=cmap,
                                   norm=norm,
                                   orientation='vertical')
        #change text font size
        for label in (ax.get_xticklabels() + ax.get_yticklabels()):
            label.set_fontsize(9)
        for label in (ax1.get_xticklabels() + ax1.get_yticklabels()):
            label.set_fontsize(9)

    try:
        if(param == ''):
            tsData = "Sorry, no parameters found.";

        elif(str(attr).lower() == 'and'):
            clientID = 1;
                
        else:
            tsData = "No data for this client"
    
    except Exception, Err:
        tsData = "Sorry, Cannot return time series. ";
        curs.close()
        #pgconn.close()
        return HttpResponse(str(tsData));

    finally:
        #tsData = data1
        plt.close('all')
        if mode == 'surface':
            ####this will return png image
            #canvas = FigureCanvasAgg(fig)
            #response = HttpResponse(content_type='image/png')
            #canvas.print_png(response)            
            #this is for encoding on the browser -- didn't want to create an image on the server
            io = StringIO()
            fig.savefig(io, format='png',bbox_inches='tight',pad_inches=0.2)
            data = io.getvalue().encode('base64')
            
            return HttpResponse(data)
            #return response
                
        else:
            return HttpResponse(str(tsData))

#===============================================================================
# Request time series for start and end date profile
#===============================================================================
def gettimeseries(request):
    ##sensor dictionary
    paramaterDic = {'current_speed':['cm/s',1,'Current Speed'],'current_direction':['degrees',2,'Current Direction'],'atmospheric_pressure':['mBar',3,'Mean Atmospheric Pressure'],'humidity':['%',4,'Mean Humidity'],'rain':['mm',5,'Rain Amount'],'air_temp':['C',6,'Air Temperature'],'wind_speed_10m_max':['m/s',7,'Maximum 10m Wind Speed'],'wind_speed_1_5m_max':['m/s',8,'Maximum 1.5m Wind Speed'],'wind_direction_10m':['TN',9,'Mean 10m Wind Direction'],'wind_direction_1_5m':['TN',10,'Mean 1.5m Wind Direction'],'wind_speed_10m_mean':['m/s',11,'Mean 10m Wind Speed'],'wind_speed_1_5m_mean':['m/s',12,'Mean 1.5m Wind Speed'],'vert_wind_speed_max':['m/s',13,'Maximum Vertical Wind Speed'],'vert_wind_speed_mean':['m/s',14,'Mean Vertical Wind Speed'],'vert_wind_speed_min':['m/s',15,'Minimum Vertical Wind Speed'],'salinity':['psu',16,'Water Salinity'],'sound_velocity':['m/s',17,'Sound Velocity'],'density':['kg/m3',18,'Density'],'turbidity':['NTU',19,'Turbidity'],'water_temp':['C',20,'Mean Water Temperature'],'height':['m',21,'Surface Elevation'],'voltage':['V',22,'Voltage from Tide'],'tide_height':['m',23,'Tide Height'],'wave_height':['m',24,'Wave Height'],'wave_period':['seconds',25,'Wave Period'],'wave_direction':['degrees',26,'Wave Direction']}
    
    attr = request.GET['attr']
    #depthindex = request.GET['depthindex']
    stationID = request.GET['st']
    startTime = request.GET['starttime'].upper()
    endTime = request.GET['endtime'].upper()
    mode = request.GET['y']

    try:
        sampledata = request.GET['samp'];  
    except:
        sampledata = 'true';
    
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
        #pgconn = pgs.connect(user="postgres",password="PinkPanther#3",host="localhost",port='5432',dbname="oceansmap_obs")
        #curs = pgconn.cursor()
        curs = connections['default'].cursor()
    except:
        return HttpResponse("Sorry, Cannot Connect to Data.")
        
    tsData = []
             
    try:
        if(param == ''):
            tsData = "Sorry, no parameters found.";

        elif(str(attr).lower() == 'and'):
            #just anadarko now
            clientID = 1;

            if(sampledata == 'true'):
                curs.execute("select collection_date, depth "+param+ " from data.data_values_1h where station_id="+stationID+" and collection_date > '"+ startTime +"' and collection_date < '"+ endTime+ "';");
            else:
                curs.execute("select collection_date, depth "+param+ " from data.data_values where station_id="+stationID+" and collection_date > '"+ startTime +"' and collection_date < '"+ endTime+ "';");                            

            rows_serial = json.dumps(curs.fetchall(), cls=DjangoJSONEncoder);
            rows_json = json.loads(rows_serial)
            
            curs.close()
            #pgconn.close()
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
        curs.close()
        #pgconn.close()
        tsData = "Sorry, Cannot return time series. ";
        return HttpResponse(str(tsData))
    finally:
        if mode == 'surface':
            if type(response) == str:
                return HttpResponse(response)
            else:
                return response
        else:
            return HttpResponse(str(tsData))

#===============================================================================
# Request all values at specific date/time  
# input = timestamp
#===============================================================================
def getvalues(request):
    ##sensor dictionary
    paramaterDic = {'current_speed':['cm/s',1,'Current Speed'],'current_direction':['degrees',2,'Current Direction'],'atmospheric_pressure':['mBar',3,'Mean Atmospheric Pressure'],'humidity':['%',4,'Mean Humidity'],'rain':['mm',5,'Rain Amount'],'air_temp':['C',6,'Air Temperature'],'wind_speed_10m_max':['m/s',7,'Maximum 10m Wind Speed'],'wind_speed_1_5m_max':['m/s',8,'Maximum 1.5m Wind Speed'],'wind_direction_10m':['TN',9,'Mean 10m Wind Direction'],'wind_direction_1_5m':['TN',10,'Mean 1.5m Wind Direction'],'wind_speed_10m_mean':['m/s',11,'Mean 10m Wind Speed'],'wind_speed_1_5m_mean':['m/s',12,'Mean 1.5m Wind Speed'],'vert_wind_speed_max':['m/s',13,'Maximum Vertical Wind Speed'],'vert_wind_speed_mean':['m/s',14,'Mean Vertical Wind Speed'],'vert_wind_speed_min':['m/s',15,'Minimum Vertical Wind Speed'],'salinity':['psu',16,'Water Salinity'],'sound_velocity':['m/s',17,'Sound Velocity'],'density':['kg/m3',18,'Density'],'turbidity':['NTU',19,'Turbidity'],'water_temp':['C',20,'Mean Water Temperature'],'height':['m',21,'Surface Elevation'],'voltage':['V',22,'Voltage from Tide'],'tide_height':['m',23,'Tide Height'],'wave_height':['m',24,'Wave Height'],'wave_period':['seconds',25,'Wave Period'],'wave_direction':['degrees',26,'Wave Direction']}
    
    attr = request.GET['attr']
    #depthindex = request.GET['depthindex']
    #stationID = request.GET['st']
    curTime = request.GET['t'].upper()
    mode = request.GET['y']
    
    #===========================================================================
    # DB Connection.
    #===========================================================================
    try:
        #pgconn = pgs.connect(user="postgres",password="PinkPanther#3",host="localhost",port='5432',dbname="oceansmap_obs")
        #curs = pgconn.cursor()
        curs = connections['default'].cursor()
    except:
        return HttpResponse("Sorry, Cannot Connect to Data.")
        
    tsData = []
    
    curs.execute("select station_id,depth,value3,value4,value5,value6,value7,value8,value9,value10,value11,value12,value13,value14,value15,value16,value17,value18,value19,value20,value21,value22,value23,value24,value25,value26,value2,value1 from data.data_values where depth < 26 and collection_date = '"+ curTime +"' order by station_id,depth;");
    
    rows_serial = json.dumps(curs.fetchall(), cls=DjangoJSONEncoder);
    curs.close()
    #pgconn.close()
    #this is to format json based on the number of parameters
    rows_json = json.loads(rows_serial)
    
    objects_output = [];
    collection_list= ordereddict.OrderedDict();

    for row in rows_json:

        stationblock = ordereddict.OrderedDict();
        #filter out the duplicate values at depth and choose the closest to the surface
        if(len(objects_output)>0):
            prev = objects_output[-1];         
            if(prev['sid'] == row[0]):
                if(prev['Depth']< row[1]):
                    objects_output.pop();
                else:
                    #add variables to block
                    objects_output.pop();
                    stationblock = prev;

        stationblock['sid'] = row[0];
        stationblock['Depth'] = row[1];

        if(row[26] is not None):
            stationblock['Current Direction'] = round(float(row[26]),2)
        if(row[27] is not None):
            stationblock['Current Speed'] = round(float(row[27]),2)
        if(row[2] is not None):
            stationblock['Pressure'] = str(round(float(row[2]),2)) + ' mBar'
        if(row[3] is not None):
            stationblock['Humidity'] = str(round(float(row[3]),2))  +' %'
        if(row[4] is not None):
            stationblock['Rain'] = str(round(float(row[4]),2)) + ' mm'
        if(row[5] is not None):
            stationblock['Air Temp'] = str(round(float(row[5]),2)) + ' C'
        if(row[6] is not None):
            stationblock['Max Wind Speed 10m'] = str(round(float(row[6]),2)) + ' m/s'
        if(row[7] is not None):
            stationblock['Max Wind Speed 1.5m'] = str(round(float(row[7]),2)) + ' m/s'
        if(row[8] is not None):
            stationblock['Wind Direction 10m'] = str(round(float(row[8]),2)) + ' degrees'
        if(row[9] is not None):
            stationblock['Wind Direction 1.5m'] = str(round(float(row[9]),2)) + ' degrees'
        if(row[10] is not None):
            stationblock['Mean Wind Speed 10m'] = str(round(float(row[10]),2)) + ' m/s'
        if(row[11] is not None):
            stationblock['Mean Wind Speed 1.5m'] = str(round(float(row[11]),2)) + ' m/s'
        if(row[12] is not None):
            stationblock['Max Vertical Wind Speed'] = str(round(float(row[12]),2)) + ' m/s'
        if(row[13] is not None):
            stationblock['Mean Vertical Wind Speed'] = str(round(float(row[13]),2)) + ' m/s'
        if(row[14] is not None):
            stationblock['Min Vertical Wind Speed'] = str(round(float(row[14]),2)) + ' m/s'
        if(row[15] is not None):
            stationblock['Salinity'] = str(round(float(row[15]),2)) + ' psu'
        if(row[16] is not None):
            stationblock['Sound Velocity'] = str(round(float(row[16]),2)) + ' m/s'
        if(row[17] is not None):
            stationblock['Density'] = str(round(float(row[17]),2)) + ' kg/m3'
        if(row[18] is not None):
            stationblock['Turbidity'] = str(round(float(row[18]),2)) + ' NTU'
        if(row[19] is not None):
            stationblock['Water Temp'] = str(round(float(row[19]),2)) + ' C'
        if(row[20] is not None):
            stationblock['Surface Elevation'] = str(round(float(row[20]),2)) + ' m'
        if(row[21] is not None):
            stationblock['Voltage'] = str(round(float(row[21]),2)) + ' V'
        if(row[22] is not None):
            stationblock['Tide Height'] = str(round(float(row[22]),2)) + ' m'
        if(row[23] is not None):
            stationblock['Wave Height'] = str(round(float(row[23]),2)) + ' m'
        if(row[24] is not None):
            stationblock['Wave Period'] = str(round(float(row[24]),2)) + ' seconds'
        if(row[25] is not None):
            stationblock['Wave Direction'] = str(round(float(row[25]),2)) + ' degrees'
        
        if(len(stationblock)>2):
            objects_output.append(stationblock)       

    collection_list['values']= objects_output;
    collection_list['time'] = curTime;
    tsData = json.dumps(collection_list)

    try:
        if(str(attr).lower() == 'and'):
            #just anadarko now
            clientID = 1;
        
        else:
            tsData = "No data for this client"
    
    except Exception, Err:
        curs.close()
        #pgconn.close()
        tsData = "Sorry, Cannot return time series. ";
        return HttpResponse(str(tsData))
    finally:
        if mode == 'surface':
            if type(response) == str:
                return HttpResponse(response)
            else:
                return response
        else:
            return HttpResponse(str(tsData))
