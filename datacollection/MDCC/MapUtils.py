#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sat Dec  8 23:11:23 2018

@author: yongyongwei
"""
from  shapely.geometry import Point, Polygon, LineString,MultiPolygon
import shapely.geometry as geometry
import math
import json
from pprint import pprint
import matplotlib.pyplot as plt
import os,sys,glob,GPy
import pickle
import numpy as np
import pandas as pd
import copy
from scipy.stats import norm
from collections import Counter
from collections import namedtuple  
import itertools
import matplotlib.path as mplPath
from descartes.patch import PolygonPatch
from matplotlib.collections import LineCollection
from shapely.ops import cascaded_union, polygonize
from scipy.spatial import Delaunay

def frange(start, end, step):
    """Generate a sequence
    
    Args:
        start -- the start element
        end -- the end element
        step -- step length
    
    Returns:
        A sequence of numbers 
    """
    ret = []
    tmp = start
    ret.append(tmp)
    while(tmp < end):
        tmp += step
        ret.append(tmp)
    return ret

def distance(lat1,lon1,lat2,lon2):
    """Distance between two GPS point"""
    radius = 6378.137 # km
    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
          * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = radius * c
    return d*1000

def offset_coord(lat0,lon0,lat1,lon1):
    """Compute the offset of the seond GPS point relative to the first point
    Args:
        lat0,lon0 -- the latitude and longittude of the first GPS point
        lat1,lon1 -- the latitude and longittude of the second GPS point
        
    Returns:
        offset coordinate in meters
    """
    x_project = (lat0,lon1)
    y_project = (lat1,lon0)
    x_offset = distance(lat0,lon0,x_project[0],x_project[1])
    y_offset = distance(lat0,lon0,y_project[0],y_project[1])
    #if at the south of then flip the sign
    if lat1 < lat0:
        y_offset = y_offset * (-1)
    #if at the west of then flip the sign
    if lon1 < lon0:
        x_offset = x_offset * (-1)
    return (x_offset, y_offset)

def gps_fromxy(lat0,lon0,x_offset,y_offset):
    """ Convert back to the GPS cooridnate system from the local system.
    Args:
        lat0,lon0: latitude and longitude of the reference point(origin)
        x_offset,y_offset: The offset in X-axis and Y-axis
    Returns:
        GPS cooridnate(longitude and latitude)
    """
    R = 6378137.0
    #offset in radians
    dlat = y_offset/R
    dlon = x_offset/(R * math.cos(math.pi * lat0 /180.0))
    #offset gps in decimal degrees
    lat1 = lat0 + dlat * 180/math.pi
    lon1 = lon0 + dlon * 180/math.pi
    return (lon1,lat1)


MAP_FILES_FOLDER = os.path.abspath('MapFiles')
EXCLUDED_BUILDINGS=['HSC','CSB','ADL','Stadium','Les Prince Hall',\
                    'Bates Residence','Moulton Hall','Hedden Hall','MEK',\
                    'Brandon Hall','TA','NRB','Woodstock Hall','Edwards Hall',\
                    'Wallingford Hall','Matthews Hall','McKay Hall',\
                    'Whidden Hall','UHB','RJS',\
                     #Buildings have floor plan but not nessesary
                    'Alumni House','Alumni Memorial Hall','MMA',\
                     #Not considered this round
                    'Refectory','Green house', 'Divinity College']


MIN_OPEN_AREASIZE = 20.0

def get_building_dict(plot=False):
    """Get dict of buildings from the MapFiles"""
    with open(MAP_FILES_FOLDER+'/Campusoutline.geojson') as fin:
        geojson = json.load(fin)
    building_dict={}
    for i in range(len(geojson['features'])):
        if geojson['features'][i]['geometry']['type'] != 'Polygon':
            continue
        properties = geojson['features'][i]['properties']
        if properties['utility'] != 'building':
            continue
        if properties['name'] in EXCLUDED_BUILDINGS or \
        properties['shortname'] in EXCLUDED_BUILDINGS:
            continue
        gpspo = np.array(geojson['features'][i]['geometry']['coordinates'][0])
        building_dict[properties['shortname']] = {'name':properties['name'],\
                     'num_basement':properties['num_basement'],\
                     'num_floor':properties['num_floor'],\
                     'gpspo':gpspo,'center':(np.mean(gpspo[:,0]),np.mean(gpspo[:,1]))}
        if plot == True:
            lat0,lon0=np.amin(gpspo[:,1]),np.amin(gpspo[:,0])
            local_poly = [offset_coord(lat0,lon0,lat,lon) for lon,lat in gpspo]
            local_poly = np.array(local_poly)
            plt.close('all')
            plt.title(properties['name'])
            plt.plot(*zip(*local_poly),color='g')
            plt.pause(0.5)
    return building_dict

def dump_building_dict(building_dict,outfile):
    """Dumpe the building_dict into a json file"""
    outobj = copy.deepcopy(building_dict)
    for k in outobj:
        outobj[k]['gpspo'] = outobj[k]['gpspo'].tolist()
    with open(outfile,'w') as fout:
        json.dump(outobj,fout)
        
def plot_building_map(building_dict):
    """Display the map on a local coordinate system
    Args:
        building_dict -- the building dictionary (index, name, gpspolygon)
    """
    lat0 = np.min([np.min(building_dict[key]['gpspo'][:,1]) for key in building_dict.keys()])
    lon0 = np.min([np.min(building_dict[key]['gpspo'][:,0]) for key in building_dict.keys()])
    fig, ax = plt.subplots(1, 1, figsize=(10.5,15)) 
    for key in building_dict.keys():
        gpspo = building_dict[key]['gpspo']
        local_poly = [offset_coord(lat0,lon0,lat,lon) for lon,lat in gpspo]
        local_poly = np.array(local_poly)
        ax.plot(*zip(*local_poly),label=building_dict[key]['name'])
    #ax.legend()
    plt.show()

def get_floorbasenum(building_dict):
    """Return the total number of floors and basements"""
    floornum=0
    basenum=0
    for k in building_dict.keys():
        floornum += int(building_dict[k]['num_floor'])
        basenum += int(building_dict[k]['num_basement'])
    return (floornum,basenum)

def get_room_dict(bldname,floor,building_dict,plot=False,):
    """Get the room dict for a specific building and specific floor
    Args:
        bldname -- building short name
        floor -- floor number
        plot -- plot or not
    Returns:
        A dict for the rooms in the specific building and floor(local coordinates)
    """
    with open(MAP_FILES_FOLDER+'/layer'+str(floor)+'rooms.geojson') as fin:
        geojson = json.load(fin)    
    rooms = {}
    for i in range(len(geojson['features'])):
        assert geojson["features"][i]['geometry']['type'] == 'Polygon'
        roominfo = geojson["features"][i]
        if roominfo['properties']['building_name'] != building_dict[bldname]['name']:
            continue
        roomname=roominfo['properties']['name']
        roomgpspo = np.array(roominfo['geometry']['coordinates'][0])
        rooms[roomname] = roomgpspo
    if plot==True:
        buildinggpspo = building_dict[bldname]['gpspo']
        lat0 = np.min(buildinggpspo[:,1])
        lon0 = np.min(buildinggpspo[:,0])
        fig, ax = plt.subplots(1, 1, figsize=(12,12)) 
        buildingpolygon = np.array([offset_coord(lat0,lon0,lat,lon) for lon,lat in buildinggpspo])
        ax.plot(*zip(*buildingpolygon))
        for room in rooms:
            room_poly = np.array([offset_coord(lat0,lon0,lat,lon) for lon,lat in rooms[room]])
            ax.plot(*zip(*room_poly))
            center = np.mean(room_poly,axis=0)
            ax.text(center[0],center[1],room)
        plt.show()
    return rooms

def plot_multipolygon(mpo):
    """Plot the multipolygon"""
    fig,ax=plt.subplots(1, 1, figsize=(12,12)) 
    BLUE = '#6699cc'
    RED = '#ff3333'
    GRAY = '#999999'
    def plot_coords(ax, ob, color=GRAY, zorder=1, alpha=1):
        x, y = ob.xy
        ax.plot(x, y, 'o', color=color, zorder=zorder, alpha=alpha)
    def color_isvalid(ob, valid=BLUE, invalid=RED):
        if ob.is_valid:
            return valid
        else:
            return invalid
    for polygon in mpo:
        plot_coords(ax, polygon.exterior)
        patch = PolygonPatch(polygon, facecolor=color_isvalid(mpo), edgecolor=color_isvalid(mpo, valid=BLUE), alpha=0.5, zorder=2)
        ax.add_patch(patch)
    plt.show()    
    
def get_open_areas(building_dict, bldname,floor,threshold=0.3,plot=False):
    """Get the open areas a specific building and specific floor
    Args:
        building_dict -- the building dict information
        bldname -- building short name
        floor -- floor number
        plot -- plot or not
    Returns:
        Open areas with multipolygon (local cooridnate system)
    """
    building_gpspo = building_dict[bldname]['gpspo']
    lat0 = np.min(building_gpspo[:,1])
    lon0 = np.min(building_gpspo[:,0])
    local_poly = [offset_coord(lat0,lon0,lat,lon) for lon,lat in building_gpspo]
    local_poly = np.array(local_poly)
    
    roomdict = get_room_dict(bldname,floor,building_dict)
    roomdict_localcoord= copy.copy(roomdict)
    for room in roomdict_localcoord:
        roomdict_localcoord[room] = np.array([offset_coord(lat0,lon0,lat,lon) for lon,lat in roomdict_localcoord[room]])
    
    polygons = []
    for room in roomdict_localcoord:
        #polygon = Polygon(i)
        po= roomdict_localcoord[room]
        polygon = Polygon(po).buffer(threshold, resolution=16, cap_style=2, join_style=3, mitre_limit=0.1)
        polygons.append(polygon)        
    casu = cascaded_union(polygons)
    
    openarea = Polygon(local_poly).difference(casu)
    openarea = openarea.buffer(threshold, resolution=16, cap_style=2, join_style=3, mitre_limit=0.1)
    
    areapolys=[]
    for p in openarea:
        if p.area > MIN_OPEN_AREASIZE:
            areapolys.append(p)
    retarea = MultiPolygon(areapolys)
    
    if plot==True:  
        plot_multipolygon(retarea)
    return retarea

def get_gps_multipolygon(areas,lat0,lon0):
    """Get the GPS cooridnate from the areas of local cooridnate system
    Args:
        areas: multiplygon in the local coordinate sytem
        lat0,lon0: the latitude and longtitude of the reference point(origin)
    Returns:
        Multipolygon with GPS cooridnate
    """
    gpspolys=[]
    for p in areas:
        gpsexterior = [gps_fromxy(lat0,lon0,x,y) for x,y in p.exterior.coords]
        gpsinteriors = []
        for i in range(len(p.interiors)):
            interior = p.interiors[i]
            gpsinterior = [gps_fromxy(lat0,lon0,x,y) for x,y in interior.coords]
            gpsinteriors.append(gpsinterior)
        gpspolygon = Polygon(gpsexterior,gpsinteriors)
        gpspolys.append(gpspolygon)
    
    return MultiPolygon(gpspolys)

def divide_area_intocells(areas,grid_step=1.0,plot=False):
    """Divide the areas into grid cells
    Args:
        areas: multipolygon(local cooridnate sytem), the areas
        grid_step: the size of grid
        plot: plot or not
    Returns:
        List of squares (local coordinate system)
    """
    minx, miny, maxx, maxy = areas.bounds
    mesh = np.meshgrid(frange(minx,maxx,grid_step),frange(miny,maxy,grid_step))
    grid_coords = np.column_stack((np.ravel(mesh[0]),np.ravel(mesh[1])))
    valid_coords = []
    for loc in grid_coords:
        if areas.contains(Point(loc[0],loc[1])):
            valid_coords.append(loc.tolist())
    cells=[]
    for coord in valid_coords:
        cellcoord = [(coord[0]-0.5*grid_step,coord[1]-0.5*grid_step),
                     (coord[0]+0.5*grid_step,coord[1]-0.5*grid_step),
                     (coord[0]+0.5*grid_step,coord[1]+0.5*grid_step),
                     (coord[0]-0.5*grid_step,coord[1]+0.5*grid_step),
                     (coord[0]-0.5*grid_step,coord[1]-0.5*grid_step)
                    ]
        cellpoly = Polygon(cellcoord)
        if areas.contains(cellpoly):
            cells.append(cellcoord)
    
    if plot==True:     
        fig,ax=plt.subplots(1, 1, figsize=(12,12)) 
        BLUE = '#6699cc'
        RED = '#ff3333'
        GRAY = '#999999'
        def plot_coords(ax, ob, color=GRAY, zorder=1, alpha=1):
            x, y = ob.xy
            ax.plot(x, y, 'o', color=color, zorder=zorder, alpha=alpha)
            
        def color_isvalid(ob, valid=BLUE, invalid=RED):
            if ob.is_valid:
                return valid
            else:
                return invalid
        for polygon in areas:
            plot_coords(ax, polygon.exterior)
            patch = PolygonPatch(polygon, facecolor=color_isvalid(areas), edgecolor=color_isvalid(areas, valid=BLUE), alpha=0.5, zorder=2)
            ax.add_patch(patch)
        for cell in cells:
            ax.plot(*zip(*cell))
        plt.show()
        
    return cells
   
def get_building_reforigin(name, buildingprofile = 'building_dict.json'):
    """Get the GPS reference origin for buildings
    
    Currently it is the mimimum value of the building GPS polygon outline
    
    Args:
        name - building name
        buildingprofile - the outline file for the buildings

    Returns:
        (longitude, latitude) of the selected reference origin point
    """
    #dir_path = os.path.dirname(os.path.realpath(__file__))
    #buildingprofile = os.path.join(dir_path, buildingprofile)
    #Load the building dictionary
    with open(buildingprofile) as fin:
        building_dict = json.load(fin)
    #Be careful about the format of gpspo, longitude first
    gpspo = np.array(building_dict[name]['gpspo'])
    return tuple(np.min(gpspo,axis=0))

def get_building_gpspolygon(name, buildingprofile = 'building_dict.json'):
    """Get the building GPS polygon
    Args:
        name - building name
        buildingprofile - the outline file for the buildings
        
    Returns:
        numpy array of the GPS polygon
        [[longitude,latitude]...]
    """
    #dir_path = os.path.dirname(os.path.realpath(__file__))
    #buildingprofile = os.path.join(dir_path, buildingprofile)
    #Load the building dictionary
    with open(buildingprofile) as fin:
        building_dict = json.load(fin)
    return np.array(building_dict[name]['gpspo'])

def get_local_rfpoints(lat0,lon0,gpspo,grid_step=1,plot=True):
    """Convert the gps polygon to local polygon and generate reference points
       for localization 
    
    Pay attention to the format of gpspo, longitude first, then latitude
    
    Args:
        lat0, lon0 -- the latitude and longtitude of the origin (reference)
        gpspo -- the GPS polygon
        grid_step -- the grid step for the referece points
        plot -- plot or not
    """
    local_coords = [offset_coord(lat0,lon0,lat,lon) for lon,lat in gpspo]
    local_coords = np.array(local_coords)
    min_X, min_Y, max_X, max_Y = (np.amin(local_coords[:,0]), np.amin(local_coords[:,1]), np.amax(local_coords[:,0]), np.max(local_coords[:,1]))
    mesh = np.meshgrid(frange(min_X,max_X,grid_step),frange(min_Y,max_Y,grid_step))
    grid_coords = np.column_stack((np.ravel(mesh[0]),np.ravel(mesh[1])))
    shape_polygon = Polygon(local_coords)
    valid_coords = []
    valid_points = []
    for loc in grid_coords:
        if shape_polygon.contains(Point(loc[0],loc[1])):
            valid_coords.append(loc)
            valid_points.append(loc.tolist())
    valid_coords = np.array(valid_coords)
    
    if plot==True:
        plt.plot(*zip(*local_coords))
        plt.scatter(valid_coords[:,0],valid_coords[:,1],color='r',marker='*')
    return valid_points
     

if __name__=='__main__':
    buildingname='ITB'
    floor=1
    building_dict=get_building_dict()
    plot_building_map(building_dict)
    areas = get_open_areas(building_dict, buildingname,floor,plot=True)
    divide_area_intocells(areas,grid_step=1.0,plot=True)
    
    

    dump_building_dict(building_dict,'building_dict.json')     
    
    name= 'ITB'
    origin = get_building_reforigin(name)
    gpspo = get_building_gpspolygon(name)
    get_local_rfpoints(origin[1],origin[0],gpspo)
    
