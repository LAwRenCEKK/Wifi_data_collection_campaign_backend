#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sat Dec  8 23:11:23 2018

@author: yongyongwei
"""
import sys
sys.dont_write_bytecode = True
import os
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors,cm

import Data_pb2
import MapUtils

#import datacollection.MDCC.Data_pb2 as Data_pd2
#import datacollection.MDCC.MapUtils as MapUtils
import glob
import geojson
from geojson import FeatureCollection,Feature,Point


def location_interpolate(start, terminal, step_events, timestamp, steplen=None):
    """Interpolate the location during walking
    
    Args:
        start: The start location, type: Data_pb2.LatLon (GPS coordinate)
        terminal: The terminal location, type: Data_pb2.LatLon (GPS coordinate)
        step_events: Step event timestamps array, microsecond since boot
        timestamp: timestamp needs location query
        
    Returns:
        (latitude,longitude) <GPS coordinate>
    """
    start_latitude = start.latitude
    start_longitude = start.longitude
    terminal_latitude = terminal.latitude
    terminal_longitude = terminal.longitude
    pathlength = MapUtils.distance(start_latitude,start_longitude,
                                   terminal_latitude,terminal_longitude)
    #Get step length if not set from the paramater
    if (steplen == None):
        stepnum = len(step_events)
        steplen = pathlength*1.0/stepnum
    #Exceptinal case
    if timestamp < step_events[0]:
        #print("timestamp %ld less than start step event\n" % timestamp)
        return None
    if timestamp >= step_events[-1]:
        #print("timestamp %ld more than terminal step event\n" % timestamp)
        return None
    #Interpolate
    int_steps=0
    for steptime in step_events:
        if timestamp >= steptime:
            int_steps += 1
        else:
            break
    partial_steps = (timestamp - step_events[int_steps-1] )* 1.0  /  \
                    (step_events[int_steps] - step_events[int_steps-1])
    
    walklength = (int_steps + partial_steps) * steplen
    ratio = walklength/pathlength
    total_xoffset, total_yoffset = MapUtils.offset_coord(start_latitude,\
                        start_longitude,terminal_latitude,terminal_longitude)
    #Note the return of gps_fromxy is lon,lat
    reslon,reslat = MapUtils.gps_fromxy(start_latitude,start_longitude,\
                                   ratio * total_xoffset,ratio * total_yoffset)
    
    return (reslon,reslat)
    
def get_labeled_rss(datapack,bssid = None):
    """Get location (GPS) labled rss from datapack
    Args:
        datapack: Data package object
        bssid: Only extract the selected bssid
    Returns:
        List of labeled rss
    """
    ret = []
    for item in datapack.rssItems:
        if bssid != None and item.bssid != bssid:
            continue
        if datapack.collectMode != 2:
            label = location_interpolate(datapack.startLocation, \
                    datapack.terminalLocation, datapack.stepEvents, item.timestamp)    
        else:
            label = (datapack.startLocation.longitude,datapack.startLocation.latitude)
        #Note the label can be failed
        if label == None:
            continue
        ret.append([item.scanNum,item.timestamp,item.bssid,item.level, \
                    item.frequency,label[0],label[1]]) 
    #Endfor
    return ret
        
def get_labeled_mag(datapack,magnitude = False):
    """Get location (GPS)  labled magnetic field signal"""
    ret = []
    for item in datapack.magnetic:
        if datapack.collectMode != 2:
            label = location_interpolate(datapack.startLocation,\
                    datapack.terminalLocation, datapack.stepEvents,item.timestamp)
        else:
            label = (datapack.startLocation.longitude,datapack.startLocation.latitude)
        if label == None:
            continue
        if magnitude == False:
            ret.append([item.x,item.y,item.z,item.timestamp,label[0],label[1]])
        else:
            magmag = np.sqrt(item.x*item.x + item.y*item.y + item.z*item.z)
            ret.append([magmag,item.timestamp,label[0],label[1]])
    #Endfor
    return ret

def get_labeled_light(datapack):
    """Get location (GPS) labeled light sensor values"""
    ret = []
    for item in datapack.light:
        if datapack.collectMode != 2:
            label = location_interpolate(datapack.startLocation,\
                    datapack.terminalLocation, datapack.stepEvents,item.timestamp)
        else:
            label = (datapack.startLocation.longitude,datapack.startLocation.latitude)
        if label == None:
            continue
        ret.append([item.value,item.timestamp,label[0],label[1]])
    #Endfor
    return ret    
    
def get_statistics(datapack):
    """Retrieve statistic information for data package"""
    info={}
    info['collectMode'] = datapack.collectMode
    info['duration'] = (datapack.terminalTime - datapack.startTime)/1000.0
    info['numofscan'] = datapack.rssItems[-1].scanNum
    info['lightsize'] = len(datapack.light)
    info['magsize'] = len(datapack.magnetic)
    bssids = set()
    bssids2G = set()
    bssids5G = set()
    rss2GNum = 0
    rss5GNum = 0
    for item in datapack.rssItems:
        bssids.add(item.bssid)
        if item.frequency > 3000:
            bssids5G.add(item.bssid)
            rss5GNum += 1
        else:
            bssids2G.add(item.bssid)
            rss2GNum +=1
    info['numofbssid'] = len(bssids)
    info['bssids'] = bssids
    
    info['bssids2G'] = bssids2G
    info['bssids5G'] = bssids5G
    info['rss2GNum'] = rss2GNum
    info['rss5GNum'] = rss5GNum
    
    if datapack.collectMode !=2:
        info['numofstep'] = len(datapack.stepEvents)
        start_latitude = datapack.startLocation.latitude
        start_longitude = datapack.startLocation.longitude
        terminal_latitude = datapack.terminalLocation.latitude
        terminal_longitude = datapack.terminalLocation.longitude
        pathlength = MapUtils.distance(start_latitude,start_longitude,\
                                       terminal_latitude,terminal_longitude)
        info['pathlen'] = pathlength
        info['speed'] = pathlength/info['duration']
        
    #Endif
    return info

def merge_packages(datapacks,fptype):
    """Merge the data packages and extract the fingperints
    
    Args:
        datapacks - list of data package
        fptype - fingerprint type,i.e., "wifi","magnetic" or "light"
        
    Returns:
        For WiFi, return a dict of list organized by bssid; otherwise item list
    """
    #Building Check
    building_names = set()
    for pack in datapacks:
        if len(pack.buildingName)>0:
            building_names.add(pack.buildingName)
    assert len(building_names) == 1, "Packages must be from the same building"
    assert fptype in ["wifi","light","magnetic"], "fptype invalid"    
    data = []
    for datapack in datapacks:
        if fptype == "wifi":
            wifi = get_labeled_rss(datapack)
            data.extend(wifi)
        elif fptype == "light":
            light = get_labeled_light(datapack)
            data.extend(light)
        elif fptype == "magnetic":
            #Note the magnetic is magnitude, so it is a scalar
            magnetic = get_labeled_mag(datapack,magnitude=True)
            data.extend(magnetic)
    if fptype == "wifi":
        APs = set([item[2] for item in data])
        data_byAP={AP:[] for AP in APs}
        for entry in data:
            data_byAP[entry[2]].append([entry[5],entry[6],entry[3],entry[4]])
        return data_byAP
    else:
        #Note the format
        return [[entry[2],entry[3],entry[0]] for entry in data]
        

def rss_positions(datapacks,outfile=None):
    """Extract the all the gps positions from  the datapacks
    
    Args:
        datapacks - a list of datapack
        outfile - output file name
    Returns:
        if outfile == None, return the geojson string directly, otherwise write
    """       
    crs = geojson.crs.Named("urn:ogc:def:crs:OGC:1.3:CRS84")
    features = []
    for datapack in datapacks:
        weight = 1
        if datapack.collectMode == 2:
            weight = 5
        labeled_rss = get_labeled_rss(datapack)
        positions = set([(item[5],item[6]) for item in labeled_rss])
        for position in positions:
            features.append(Feature(geometry=Point(position),properties={"weight":weight}))
    #endfor
    collection = FeatureCollection(features,crs = crs)
    if outfile == None:
        return geojson.dumps(collection)
    else:
        with open(outfile,'w') as fout:
            geojson.dump(collection,fout)
    
def surveyed_positions(datapacks,outfile = None):
    """Extract the step positions from the datapacks
    
    For the purpose of heatmap on mobile side
    
    Args:
        datapacks - the datapacks list
    Returns:
        if outfile == None, return the geojson string directly, otherwise write
    """
    crs = geojson.crs.Named("urn:ogc:def:crs:OGC:1.3:CRS84")
    features = []
    for datapack in datapacks:
        if datapack.collectMode == 2:
            weight = 5
            point_pos = (datapack.startLocation.longitude,datapack.startLocation.latitude)
            features.append(Feature(geometry=Point(point_pos),properties={"weight":weight}))
        else:
            weight = 1
            for steptime in datapack.stepEvents:
                step_pos = location_interpolate(datapack.startLocation, \
                    datapack.terminalLocation, datapack.stepEvents,steptime)
                if step_pos != None:
                    features.append(Feature(geometry=Point(step_pos),properties={"weight":weight}))
    #endfor
    collection = FeatureCollection(features,crs = crs)
    if outfile == None:
        return geojson.dumps(collection)
    else:
        with open(outfile,'w') as fout:
            geojson.dump(collection,fout)                    
                    
#Data Visualization Section----------------------------------------------------
def plot_data(datapacks, fptype='wifi',bssid= None,buildingprofile='building_dict.json'):
    """Visualize the fingerprint data
    
    Args:
        datapacks: path data packages (list)
        fptype: fingerprint to visualize, wifi, magnetic or light
        buidlingprofile: building information file
    """
    if fptype == "wifi":
        assert bssid != None, "please provide the bssid"
    #Get building name (all data packages are from the same building)
    building_name = datapacks[0].buildingName
    building_dict = None
    with open(buildingprofile) as fin:
        building_dict = json.load(fin)
    gpspo = building_dict[building_name]['gpspo']
    origin_lon,origin_lat = np.min(gpspo,axis=0).tolist()
    localpo = [MapUtils.offset_coord(origin_lat,origin_lon,lat,lon) for \
               lon,lat in gpspo]  
    fig, ax = plt.subplots(1, 1, figsize=(10,8)) 
    #Plot the building first
    ax.plot(*zip(*localpo))
    #Draw the paths
    for datapack in datapacks:
        if datapack.collectMode == 2:
            continue
        start_pos = MapUtils.offset_coord(origin_lat,origin_lon,\
            datapack.startLocation.latitude,datapack.startLocation.longitude)
        stop_pos = MapUtils.offset_coord(origin_lat,origin_lon,\
            datapack.terminalLocation.latitude,datapack.terminalLocation.longitude)
        ax.arrow(start_pos[0],start_pos[1],stop_pos[0] - start_pos[0], \
                  stop_pos[1]-start_pos[1],\
                  head_width=1, head_length=1,linestyle='--')
        """#Not nessesary to draw the steps (a step is too short)
        numofstep = len(datapack.stepEvents)
        for i in range(1,numofstep):
            ax.scatter(start_pos[0] + (stop_pos[0] - start_pos[0])*i/numofstep,\
                       start_pos[1] + (stop_pos[1] - start_pos[1])*i/numofstep,\
                       s=1)
        """
    #Endfor
    data = merge_packages(datapacks,fptype)
    #Format visualization data
    visdata = None
    if fptype == "wifi":
        #gpsrss = [[item[5],item[6],item[3]] for item in data if item[2] == bssid ]
        gpsrss = [[item[0],item[1],item[2]] for item in data[bssid]]
        localrss = []
        for rss in gpsrss:
            localpos = MapUtils.offset_coord(origin_lat,origin_lon,\
                                             rss[1],rss[0])
            localrss.append([localpos[0],localpos[1],rss[2]])
        visdata = np.array(localrss)
    #For light and magnetic the same format apply
    else:
        localdata = []
        for entry in data:
            localpos = MapUtils.offset_coord(origin_lat,origin_lon,\
                                             entry[1],entry[0])
            localdata.append([localpos[0],localpos[1],entry[2]])
        visdata = np.array(localdata)
    #Plot
    xs = np.array(visdata[:,0])
    ys = np.array(visdata[:,1])
    zs = np.array(visdata[:,2])
    
    jet = plt.get_cmap('jet') 
    cNorm  = colors.Normalize(vmin=np.nanmin(zs), vmax=np.nanmax(zs))
    scalarMap = cm.ScalarMappable(norm=cNorm, cmap=jet)
            
    ax.scatter(xs, ys, color=scalarMap.to_rgba(zs), marker='o')
    scalarMap.set_array(zs)
    fig.colorbar(scalarMap)

    ax.set_xlabel('X Label')
    ax.set_ylabel('Y Label')
    title = fptype+" distribution"
    if bssid != None:
        title = title + "("+bssid+","+str(len(zs))+")"
    plt.title(title)
    plt.show()    

def plot_wifi(datapacks,sigtype="bssids2G",buildingprofile='building_dict.json'):
    bssids2G=[]
    bssids5G=[]
    for datapack in datapacks:
        bssids2G.extend(get_statistics(datapack)['bssids2G'])
        bssids5G.extend(get_statistics(datapack)['bssids5G'])
    bssids2G=set(bssids2G)
    bssids5G=set(bssids5G)
    if sigtype == "bssids2G":
        for bssid in bssids2G:
            plt.close('all')
            plot_data(datapacks,bssid= bssid,buildingprofile='building_dict.json')
            plt.pause(0.5)
        plt.close('all')
            
    elif sigtype == "bssids5G":
        for bssid in bssids5G:
            plt.close('all')
            plot_data(datapacks,bssid= bssid,buildingprofile='building_dict.json')
            plt.pause(0.5)
        plt.close('all')
            
            
#-------Utils For Files-------------------------------------------------------
def get_file_list(folder, mode):
    """Get fingerprint file list inside a folder
    Args:
        folder - folder of fingerprint files
        mode - collect mode, 1: path based, 2: point-based
    Returns:
        List of filenames of the specified files inside the folder
    """
    all_files = glob.glob(folder+"/*.pbf")
    fp_files = []
    for fname in all_files:
        if "Calibration" in fname:#Ignore calibration file
            continue
        parts = os.path.basename(fname).split('_')
        if len(parts) == 3 and int(parts[1]) == mode:
            fp_files.append(fname)
    #Replace with full paths
    return [os.path.realpath(f) for f in fp_files]

def get_floor_files(folder,floor,mode):
    """Get the files for specific floor
    
    Args:
        folder - the top folder
        floor - the specific floor (string)
        mode - collect mode
    Returns:
        List of files in the floor with mode
    """
    buildings = [ name for name in os.listdir(folder) if os.path.isdir(os.path.join(folder, name))]
    files = []
    for building in buildings:
        subfolder = os.path.join(folder,building,floor)
        files.extend(get_file_list(subfolder, mode))
    return files
    
    
def load_data_packs(filelist):
    """Load the data packages from the file list
    Args:
        filelist - a list of file packs
    Returns:
        a list of data packages
    """
    datapacks = []
    for f in filelist:
        #print('loading:',f)
        datapack = Data_pb2.DataPack()
        with open(f,'rb') as fin:
            datapack.ParseFromString(fin.read())
            datapacks.append(datapack)
    return datapacks
        
    

    
if __name__ == '__main__':
    """
    folder = 'FpData/ITB/2'
    datapacks = load_data_packs(get_file_list(folder,1))
    plot_wifi(datapacks)
    """
    
    filename = 'FpData/ITB/2/weiy49_Calibration.pbf'
    datapack = Data_pb2.DataPack()
    with open(filename,'rb') as fin:
        datapack.ParseFromString(fin.read())
      
    print(datapack.buildingName)
    print(get_statistics(datapack))
 
    """
    #Create empty layer for fp locations, note total 7 layers
    for i in range(1,8):
        surveyed_positions([],outfile=os.path.join('Heatmap','layer'+str(i)+'.geojson'))
    #For 2nd layer
    heat2files = get_floor_files('FpData','2',1) +get_floor_files('FpData','2',2)
    heat2packs = load_data_packs(heat2files)
    surveyed_positions(heat2packs,outfile=os.path.join('Heatmap','layer'+str(2)+'.geojson'))
    #For 1st layer
    heat1files = get_floor_files('FpData','1',1) +get_floor_files('FpData','1',2)
    heat1packs = load_data_packs(heat1files)
    surveyed_positions(heat1packs,outfile=os.path.join('Heatmap','layer'+str(1)+'.geojson'))
    """
