#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 11 17:04:45 2019

@author: yongyongwei

For utility calculation
"""

import sys
sys.dont_write_bytecode = True
import os

#consider replace with
#print(os.path.dirname(os.path.abspath(__file__)))
sys.path.append('/u50/liu433/ilos/mdccBackend/datacollection/MDCC')



import numpy as np
from GPy.kern import Exponential
from numpy.linalg import inv

import Data_pb2

from MapUtils import get_building_gpspolygon, get_local_rfpoints
from MapUtils import get_building_reforigin,offset_coord,gps_fromxy
from ParseData import get_file_list,load_data_packs,location_interpolate

import json,geojson
from geojson import FeatureCollection,Feature,Point


"""Define some constants"""
#grid size
GRID_STEP  = 2
#kernel parameters
VARIANCE = 50
LENSCALE = 20
NOISEVAR = 10


def condition_entropy(A, B):
    """Compute the conditional Entropy of given A of B

    Args:
        A: observed location
        B: unobserved locaton
    Returns:
        Conditional Entropy
    """
    kernel = Exponential(2, variance = VARIANCE, lengthscale =LENSCALE)
    sigmaBB = kernel.K(B,B)
    sigmaBA = kernel.K(B,A)
    sigmaAA_noise_inverse = inv((kernel.K(A,A) + NOISEVAR * np.identity(len(A))))
    cov_matrix = sigmaBB + NOISEVAR * np.identity(len(B))\
                 - np.dot(sigmaBA,np.dot(sigmaAA_noise_inverse,sigmaBA.T))
    #entropy=0.5 * np.log(((2*np.pi*np.e)**len(B)) * np.linalg.det(cov_matrix))
    sign, logdet = np.linalg.slogdet(cov_matrix)
    assert(sign == 1)
    entropy = 0.5 * (len(B) + len(B) * np.log(2*np.pi)) + 0.5 * sign *logdet
    return entropy

def entropy(B):
    """Calculate the entropy from a series of locations
    
    Args:
        B - the locations, N*2 matrix
        
    Returns: 
        The entropy
    """
    kernel = Exponential(2, variance = VARIANCE, lengthscale =LENSCALE)
    sigmaBB = kernel.K(B,B) +  NOISEVAR * np.identity(len(B))
    sign, logdet = np.linalg.slogdet(sigmaBB)
    assert(sign == 1)
    entropy = 0.5 * (len(B) + len(B) * np.log(2*np.pi)) + 0.5 * sign *logdet
    return entropy
    
def post_variance(A,B):
    """Compute the posterior (co)variance given A of B
    Args:
        A: observed locations 
        B: unobserved locations
    Retruns:
        the (co)variance (matrix)
    """  
    kernel = Exponential(2, variance = VARIANCE, lengthscale =LENSCALE)
    sigmaBB = kernel.K(B,B)
    sigmaBA = kernel.K(B,A)
    sigmaAA_noise_inverse = inv((kernel.K(A,A) + NOISEVAR * np.identity(len(A))))
    cov_matrix = sigmaBB + NOISEVAR * np.identity(len(B))\
                 - np.dot(sigmaBA,np.dot(sigmaAA_noise_inverse,sigmaBA.T))
    return cov_matrix

    
def utility_calculate(building,floor, packfile,buildingprofile='building_dict.json'):
    """Calculate the utility obtained from the package
    
    Based on reduced entropy
    
    Args:
        building - buidlding name
        floor - floor number
        packfile - the package to evaluate (only the name, does not contain any path)
        
    Returns:
        the utility obtained due to the collected data
    """
    filesfolder = os.path.join('FpData',building,str(floor))
    lon0,lat0 = get_building_reforigin(building,buildingprofile)
    building_gpspo = get_building_gpspolygon(building,buildingprofile)
    #Load data packages: consider both walking and standing
    pack_files = get_file_list(filesfolder,1) + get_file_list(filesfolder,2)
    assert(len(pack_files) >0)
    filefulpath = os.path.dirname(pack_files[0])
    if os.path.join(filefulpath,packfile) in pack_files:
        pack_files.remove(os.path.join(filefulpath,packfile))
    datapacks = load_data_packs(pack_files)
    #Extract locations
    locations_gps = []
    for datapack in datapacks:
        if datapack.collectMode == 2:
            locations_gps.append((datapack.startLocation.longitude,datapack.startLocation.latitude))
        else:
            for steptime in datapack.stepEvents:
                step_pos = location_interpolate(datapack.startLocation, \
                    datapack.terminalLocation, datapack.stepEvents,steptime)
                if step_pos != None:
                    locations_gps.append(step_pos)
    locations = np.array([offset_coord(lat0,lon0,lat,lon) for lon,lat in locations_gps])
    #Extract reference point system
    local_rfpoints = get_local_rfpoints(lat0,lon0,building_gpspo,grid_step=GRID_STEP,plot=False)
    local_rfpoints = np.array(local_rfpoints)
    if len(locations) == 0:
        init_entropy = entropy(local_rfpoints)
    else:
        init_entropy = condition_entropy(locations, local_rfpoints)
    #Load the package to be evaluated
    targetpack = Data_pb2.DataPack()
    with open(os.path.join(filefulpath,packfile),'rb') as fin:
        targetpack.ParseFromString(fin.read())
    if targetpack.collectMode == 2:
        target_gps = [[targetpack.startLocation.longitude,targetpack.startLocation.latitude]]
    else:
        target_gps = []
        for steptime in targetpack.stepEvents:
            step_pos = location_interpolate(targetpack.startLocation, \
                targetpack.terminalLocation, targetpack.stepEvents,steptime)
            if step_pos != None:
                target_gps.append(step_pos)
    target_locs = np.array([offset_coord(lat0,lon0,lat,lon) for lon,lat in target_gps])
    if len(locations) == 0:
        result_entropy = condition_entropy(target_locs, local_rfpoints)
    else:
        result_entropy = condition_entropy(np.row_stack((locations,target_locs)), local_rfpoints)
    packpoint = init_entropy - result_entropy
    #scale the point if it is a point based packet
    if targetpack.collectMode == 2:
        packpoint = packpoint * 3.0

    return packpoint
    
def rfpoints_uncertainty(floor,buildingprofile='building_dict.json',outfile=None):
    """Calculate the uncertainty of the specifc floors, used for heatmap"""
    with open(buildingprofile) as fin:
        building_dict = json.load(fin)
    crs = geojson.crs.Named("urn:ogc:def:crs:OGC:1.3:CRS84")
    features = []
    for building in building_dict.keys():
        #Ignore if the floor does not appear in the building
        if int(building_dict[building]['num_floor']) < floor:
            continue
        #Get building information
        lon0,lat0 = get_building_reforigin(building,buildingprofile)
        building_gpspo = get_building_gpspolygon(building,buildingprofile)
        #Extract reference point system
        local_rfpoints = get_local_rfpoints(lat0,lon0,building_gpspo,\
			grid_step=GRID_STEP,plot=False)
        local_rfpoints = np.array(local_rfpoints)
        #Get Fingerprint Files
        filesfolder = os.path.join('FpData',building,str(floor))
        #Extract user locations
        locations_gps = []
        if os.path.exists(filesfolder) == True:
            pack_files = get_file_list(filesfolder,1) + get_file_list(filesfolder,2)
            if len(pack_files) > 0:
                datapacks = load_data_packs(pack_files)
                for datapack in datapacks:
                    if datapack.collectMode == 2:
                        locations_gps.append((datapack.startLocation.longitude,\
					datapack.startLocation.latitude))
                    else:
                        for steptime in datapack.stepEvents:
                            step_pos = location_interpolate(datapack.startLocation, \
                                datapack.terminalLocation, datapack.stepEvents,steptime)
                            if step_pos != None:
                                locations_gps.append(step_pos)
        if len(locations_gps) > 0:
            fplocations = np.array([offset_coord(lat0,lon0,lat,lon) \
                          for lon,lat in locations_gps])
            localrf_variance = np.column_stack((local_rfpoints,\
                          np.diagonal(post_variance(fplocations,local_rfpoints))))
            localrf_entropy = np.array([0.5 * (np.log(2*np.pi*(var)) + 1) \
                                       for var in localrf_variance[:,2]])
            localrf_uncertainty = np.column_stack((local_rfpoints,localrf_entropy))
        else:
            en = 0.5 * (np.log(2*np.pi*(VARIANCE + NOISEVAR)) + 1)
            localrf_uncertainty = np.column_stack((local_rfpoints,\
                            np.repeat(en,local_rfpoints.shape[0])))
        #Convert to GPS points
        gps_rf = [gps_fromxy(lat0,lon0,x_offset,y_offset) \
                  for x_offset,y_offset in localrf_uncertainty[:,[0,1]]]
        gps_uncertainty = np.column_stack((gps_rf,localrf_uncertainty[:,2]))
        building_features = [Feature(geometry=Point([lon,lat]),\
               properties={"weight":entropy}) for lon,lat,entropy in gps_uncertainty]
        features.extend(building_features)
    #endfor building
    collection = FeatureCollection(features,crs = crs)
    if outfile == None:
        return geojson.dumps(collection)
    else:
        with open(outfile,'w') as fout:
            geojson.dump(collection,fout)     
    
if __name__ == '__main__':
    import time
    start=time.time()
    print('start:',start)
    building = 'ITB'
    floor = 2
    packfile ='weiy49_1_20190925193716.pbf'
    score= utility_calculate(building,floor, packfile)
    end=time.time()
    print('end:',end)
    print('time elapsed:',end-start)
    print("The score is ",score)
