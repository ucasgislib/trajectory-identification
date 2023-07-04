#-*- coding:utf-8 -*-

import sys
import pg
import ogr
import osr
import time
import math
import numpy as np
import pandas as pd
from rtree import index

from utils import ARCVIEW_SHAPE

class SPATIAL_REASONING(object):
    def __init__(self):
        self.shp_drv = ARCVIEW_SHAPE()

    def labeling_I(self,lng,lkd,pkd1,pkd2,Gamma=0.65):
        if lkd > Gamma*min(pkd1,pkd2):
            label = "I1"
        else:
            if lng > 150:
                label = "I2"
            else:
                label = "III22"
        return label

    def labeling_II(self,lng,pt1,pt2,lazm,pazm1,pazm2,lkd,pkd1,pkd2,Tag=27,Gamma=0.65):
        pazm = (1-pt1)*pazm1+(1-pt2)*pazm2 
        delta = max(lazm,pazm)-min(lazm,pazm)
        if delta > 180:
            delta = 360-delta
        if delta < Tag:
            if lkd > Gamma*min(pkd1,pkd2):
                if pt1 == 1:
                    label = "II11"
                else:
                    label = "II21"
            else:
                if pt1 == 1:
                    if lng > 150:
                        label = "II12"
                    else:
                        label = "III22"
                else:
                    if lng > 150:
                        label = "II22"
                    else:
                        label = "III22"
        else:
            if pt1 == 1:
                if lng > 150:
                    label = "II12"
                else:
                    label = "III22"
            else:
                if lng > 150:
                    label = "II22"
                else:
                    label = "III22"
        return label

    def labeling_III(self,lng,pt1,pt2,lazm,pazm1,pazm2,lkd,pkd1,pkd2,Tag=27,Gamma=0.65):
        delta = max(pazm1,pazm2)-min(pazm1,pazm2)
        if delta > 180:
            delta = 360-delta

        if delta < Tag:
            d1 = max(lazm,pazm1)-min(lazm,pazm1)
            if d1 > 180:
                d1 = 360-d1
            d2 = max(lazm,pazm2)-min(lazm,pazm2)
            if d2 > 180:
                d2 = 360-d2
            if max(d1,d2)<Tag:
                if lkd > Gamma*min(pkd1,pkd2):
                    label = "III11"
                else:
                    if lng > 250:
                        label = "III12"
                    else:
                        label = "III11"
            else:
                if lng > 250:
                    label = "III12"
                else:
                    label = "III11"
        else:
            label = "III21"

        return label

    def spatial_reasoning_(self,rec,Tag=27,Gamma=0.65):
        pt1,pt2 = rec["pt1"],rec["pt2"]
        lng = rec["lng"]
        lazm,pazm1,pazm2 = math.degrees(rec["lazm"]),math.degrees(rec["pazm1"]),math.degrees(rec["pazm2"])
        lkd,pkd1,pkd2 = rec["lkd"],rec["pkd1"],rec["pkd2"]
        
        if (pt1 in [-1,-2]) or (pt2 in [-1,-2]):
            label = "Unknown"
        else:
            flag = pt1+pt2
            if flag == 0:   #III
                label = self.labeling_III(lng,pt1,pt2,lazm,pazm1,pazm2,lkd,pkd1,pkd2,Tag=Tag,Gamma=Gamma)
            elif flag == 1: #II
                label = self.labeling_II(lng,pt1,pt2,lazm,pazm1,pazm2,lkd,pkd1,pkd2,Tag=Tag,Gamma=Gamma)
            elif flag == 2: #I
                label = self.labeling_I(lng,lkd,pkd1,pkd2,Gamma=Gamma)

        return label

    def spatial_reasoning(self,reclist,Tag=27,Gamma=0.65):
        labels = []
        for rec in reclist:
            label = self.spatial_reasoning_(rec,Tag=Tag,Gamma=Gamma)
            labels.append(label)
        return labels

    def run(self,infilename,outfilename,Tag=27,Gamma=0.65):

        spatialref,geomtype,geomlist,fieldlist,reclist = self.shp_drv.read_shp(infilename)

        labels = self.spatial_reasoning(reclist,Tag=Tag,Gamma=Gamma)

        i = 0
        while i<len(labels):
            reclist[i]["label"] = labels[i]
            i+=1

        fieldlist.append({'width': 10, 'type': ogr.OFTString, 'name': 'label'})

        self.shp_drv.write_shp(outfilename,[spatialref,geomtype,geomlist,fieldlist,reclist])
                
if __name__ == '__main__':
    if len(sys.argv) != 5:
        print ("Usage: python step7_link_spatial_reasoning.py <tracking_links> <labeled> <Tag> <Gamma>")
        print ("Example: python step7_link_spatial_reasoning.py ./data/tracking_links.shp ./data/tracking_links.shp 27 0.65")
    else:
        test = SPATIAL_REASONING()
        infilename,outfilename,Tag,Gamma = sys.argv[1],sys.argv[2],float(sys.argv[3]),float(sys.argv[4])
        # infilename = "./data/tracking_links3.shp"
        # outfilename = "./data/tracking_links6.shp" 
        # Tag = 27
        # Gamma = 0.65
        test.run(infilename,outfilename,Tag=Tag,Gamma=Gamma)
