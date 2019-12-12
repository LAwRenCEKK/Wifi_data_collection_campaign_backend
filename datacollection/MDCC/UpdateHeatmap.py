#Update the heatmap layer file of geojson
#example: /usr/bin/python3.6 UpdateHeatmap.py 1
import sys
sys.dont_write_bytecode = True
import os,optparse
import ParseData
import UtilityCalc

dest_folder = os.path.dirname(os.path.abspath(__file__))+"/../../static/heatmap"
dest_folder = os.path.abspath(dest_folder)

def update_heatmap_V0(floor):
    datafiles = ParseData.get_floor_files('FpData',str(floor),1) \
                +ParseData.get_floor_files('FpData',str(floor),2)
    datapacks = ParseData.load_data_packs(datafiles)
    print('Number of packages loaded:',len(datapacks))
    outfile = os.path.join(dest_folder,'layer'+str(floor)+'.geojson')
    ParseData.surveyed_positions(datapacks,outfile=outfile)

def update_heatmap_V1(floor,buildingprofile='building_dict.json'):
    """Update the heatmap layer based on the uncertainty of each building"""
    outfile = os.path.join(dest_folder,'layer'+str(floor)+'.geojson')
    UtilityCalc.rfpoints_uncertainty(floor,\
           buildingprofile='building_dict.json',outfile=outfile)

if __name__ == "__main__":
    parser = optparse.OptionParser(usage="%prog  floorNum")
    options, args = parser.parse_args()
    floor = int(args[0])
    print('floor:',floor)
    print(dest_folder)
    update_heatmap_V1(floor)
