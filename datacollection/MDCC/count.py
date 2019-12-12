#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sat Dec  8 23:11:23 2018

@author: yongyongwei
"""
import sys
sys.dont_write_bytecode = True
import os
import Data_pb2

import glob

data_folder = './FpData'

buildings = os.listdir(data_folder)
total_scans = 0
total_time = 0
for b in buildings:
    if os.path.isdir('./FpData/%s' % b):
        floors = os.listdir('./FpData/%s' % b)
        for f in floors:
            fpfiles = os.listdir('./FpData/%s/%s' % (b,f))
            for fpf in fpfiles:
                if len(fpf.split('_'))==3:
                    fullf = './FpData/%s/%s/%s' % (b,f,fpf)
                    print(fullf)
                    dp = Data_pb2.DataPack()
                    with open(fullf,'rb') as fin:
                        dp.ParseFromString(fin.read())
                    print('macID',dp.macID,'device',dp.deviceInfo,'total \
                    scan',dp.totalScans)
                    total_scans += dp.totalScans
                    total_time += (dp.terminalTime  - dp.startTime)

print('total scans',total_scans)
print('total time',total_time)

