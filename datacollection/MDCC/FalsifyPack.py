#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  4 13:58:32 2019

Falsify data package for performance test purpose.

@author: yongyongwei
"""
import sys
sys.dont_write_bytecode = True
import os
import json
import numpy as np
import Data_pb2
import MapUtils
import matplotlib.pyplot as plt
from  shapely.geometry import Point, Polygon

def falsify_package(input_pack_path,fake_building,fake_floor,fake_macID,building_profile = "building_dict.json",plot=False):
    """Given the input data package, falsify data package for test purpose.
    
    Args:
        input_pack_path: data package path of the input package(provide data)
        fake_building: building to fake
        fake_floor: floor to fake
        fake_macID: mac ID to fake
        building_profile: provide the building polygon information
    Returns:
        None, save the output to files
    """
    with open(building_profile) as fin:
        building_dict = json.load(fin)
    assert fake_building in building_dict.keys(), "Faked Building Name incorrect!"
    assert fake_floor <= int(building_dict[fake_building]['num_floor']),"Faked floor number wrong"
    #Read the orignal data package
    datapack = Data_pb2.DataPack()
    with open(input_pack_path,'rb') as fin:
        datapack.ParseFromString(fin.read())
    #Falsify
    datapack.macID = fake_macID
    #Find some random points inside the target building
    area = np.array(building_dict[fake_building]['gpspo'])
    po = Polygon(area)
    
    #start: center +random noise
    center_point = np.mean(area,axis=0)
    #Find start
    while True:
        x_offset,y_offset = np.random.choice(range(-10,10),2)
        new_start = MapUtils.gps_fromxy(center_point[1],\
                                        center_point[0],\
                                        x_offset,y_offset)
        if po.contains(Point(new_start)):
            break
    
    if datapack.terminalLocation.IsInitialized():
        d = MapUtils.distance(datapack.startLocation.latitude,\
                              datapack.startLocation.longitude,\
                              datapack.terminalLocation.latitude,\
                              datapack.terminalLocation.longitude)
        while True:
            theta = np.random.uniform(-np.pi,np.pi,1)[0]
            tx_offset = d * np.cos(theta)
            ty_offset = d * np.sin(theta)
            new_terminal =  MapUtils.gps_fromxy(new_start[1],\
                                        new_start[0],\
                                        tx_offset,ty_offset)
            if po.contains(Point(new_terminal)):
                break
    #Update
    datapack.startLocation.latitude = new_start[1]
    datapack.startLocation.longitude = new_start[0]
    if datapack.terminalLocation.IsInitialized():
        datapack.terminalLocation.latitude = new_terminal[1]
        datapack.terminalLocation.longitude = new_terminal[0]
    datapack.buildingName = fake_building
    datapack.floorLevel = fake_floor
    #Visulalize the result
    if plot==True:
         fig, ax = plt.subplots(1, 1, figsize=(8,6)) 
         ax.plot(*zip(*area))
         if datapack.terminalLocation.IsInitialized():
             ax.plot([new_start[0],new_terminal[0]],[new_start[1],new_terminal[1]])
         else:
             ax.plot([new_start[0]],[new_start[1]],marker='o')
         plt.show()
         
    #output
    nameparts = os.path.basename(input_pack_path).split('_')
    nameparts[0] = fake_macID
    nameparts[2] = ".".join(["0000"+nameparts[2].split('.')[0],nameparts[2].split('.')[1]])
    fakename = "_".join(nameparts)  
    print (fakename)
    
    with open(fakename,"wb") as fout:
        fout.write(datapack.SerializeToString())
    # Add return option
    return fakename 

if __name__=="__main__":
    
    #Fake a path collected data    
    input_pack_path = 'FpData/ITB/2/weiy49_1_20181217125430.pbf'
    
    fake_building = 'JHE'
    fake_floor = 2
    fake_macID = 'fakeliu433'
    
    falsify_package(input_pack_path,fake_building,fake_floor,fake_macID,building_profile = "building_dict.json",plot=False)
    
    
    #Fake a point collected data 
    input_pack_path = 'FpData/ITB/2/weiy49_2_20181217124644.pbf'
    falsify_package(input_pack_path,fake_building,fake_floor,fake_macID,building_profile = "building_dict.json",plot=False)
