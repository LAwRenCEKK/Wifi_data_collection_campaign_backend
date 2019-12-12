#import datacollection.MDCC.UtilityCalc as mdcc
import MDCC.UtilityCalc as mdcc
import os
os.chdir(os.getcwd()+"/MDCC")

building = 'ETB'    
floor = 2
packfile = 'weiy49_1_20181218131129.pbf'

score= mdcc.utility_calculate(building,floor, packfile)
print("The score is ",score)
