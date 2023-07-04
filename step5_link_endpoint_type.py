#-*- coding:utf-8 -*-

import sys
import ogr
import time
import math
import numpy as np
from rtree import index
from sklearn.model_selection import train_test_split  
from sklearn.linear_model import LogisticRegression  

from utils import ARCVIEW_SHAPE

def process(infilename,pntfilename,outfilename):
    shp_drv = ARCVIEW_SHAPE()
    
    #tracking points
    spatialref,geomtype,geomlist,fieldlist,reclist = shp_drv.read_shp(pntfilename)
    #lookup table
    lookup = {}
    for rec in reclist:
        pid,label = rec["pid"],rec["label"]
        lookup[pid] = label

    #tracking links
    spatialref,geomtype,geomlist,fieldlist,reclist = shp_drv.read_shp(infilename)

    for rec in reclist:
        rec["pt1"] = lookup[rec["pid1"]]
        rec["pt2"] = lookup[rec["pid2"]]

    #output link file, endpoint-type added
    fieldlist.append({'width': 5, 'type': ogr.OFTInteger, 'name': 'pt1'}) 
    fieldlist.append({'width': 5, 'type': ogr.OFTInteger, 'name': 'pt2'})

    shp_drv.write_shp(outfilename,[spatialref,geomtype,geomlist,fieldlist,reclist])
        
if __name__ == '__main__':
    if len(sys.argv) != 4:
        print ("Usage: python step4_link_endpoint_type.py <tracking_links> <tracking_points> <endpoint_type>")
        print ("Example: python step4_link_endpoint_type.py  ./data/tracking_links.shp ./data/tracking_points.shp ./data/tracking_links.shp")
    else:
        infilename,pntfilename,outfilename = sys.argv[1],sys.argv[2],sys.argv[3]
        # infilename="./data/tracking_links.shp" 
        # pntfilename="./data/tracking_points2.shp" 
        # outfilename="./data/tracking_links1.shp"
        process(infilename,pntfilename,outfilename)