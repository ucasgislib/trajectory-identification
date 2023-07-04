#-*- coding:utf-8 -*-

import sys
import gdal,ogr,osr
import time
import math
import traceback
import pickle
import numpy as np
from rtree import index
import matplotlib.pyplot as plt
from operator import itemgetter, attrgetter
from datetime import datetime
from scipy import interpolate
from collections import Counter
from pylab import *  
from matplotlib.font_manager import FontProperties
import scipy.stats as stats
from utils import ARCVIEW_SHAPE

def process(aoifilename,infilename,outfilename):
    shp_drv = ARCVIEW_SHAPE()

    # AOI, area of interest
    spatialref,geomtype,geomlist,fieldlist,reclist = shp_drv.read_shp(aoifilename)
    rect = ogr.CreateGeometryFromWkt(geomlist[0])
    minx,maxx,miny,maxy = rect.GetEnvelope()
    print(minx,maxx,miny,maxy)
    
    #tracking links 
    spatialref,geomtype,geomlist,fieldlist,reclist = shp_drv.read_shp(infilename)

    #extract tracking points from tracking links
    pids = {}
    for rec in reclist:
        pid1,pid2 = rec["pid1"],rec["pid2"]
        if not pids.get(pid1,None):
            if rec["x1"]>= minx and rec["x1"]<=maxx and rec["y1"]>=miny and rec["y1"]<=maxy:
                pids[pid1] = {"pid":pid1,"tid":rec["tid"],"x":rec["x1"],"y":rec["y1"],"t":rec["t1"],"m":1}
            else:
                pids[pid1] = {"pid":pid1,"tid":rec["tid"],"x":rec["x1"],"y":rec["y1"],"t":rec["t1"],"m":0}
        if not pids.get(pid2,None):
            if rec["x2"]>= minx and rec["x2"]<=maxx and rec["y2"]>=miny and rec["y2"]<=maxy:
                pids[pid2] = {"pid":pid2,"tid":rec["tid"],"x":rec["x2"],"y":rec["y2"],"t":rec["t2"],"m":1}
            else:
                pids[pid2] = {"pid":pid2,"tid":rec["tid"],"x":rec["x2"],"y":rec["y2"],"t":rec["t2"],"m":0}

    #shape organization for tracking points
    geomtype = ogr.wkbPoint
    fieldlist = [{'width': 20, 'type': ogr.OFTInteger, 'name': 'pid'}, 
                {'width': 20, 'type': ogr.OFTInteger, 'name': 'tid'}, 
                {'width': 20, 'decimal': 6, 'type': ogr.OFTReal, 'name': 'x'}, 
                {'width': 20, 'decimal': 6, 'type': ogr.OFTReal, 'name': 'y'},
                {'width': 20, 'type': ogr.OFTInteger, 'name': 't'},
                {'width': 20, 'type': ogr.OFTInteger, 'name': 'm'}]

    geomlist,reclist = [],[]
    for pid in pids:
        geomlist.append("POINT(%s %s)"%(pids[pid]["x"],pids[pid]["y"]))
        reclist.append(pids[pid])

    shp_drv.write_shp(outfilename,[spatialref,geomtype,geomlist,fieldlist,reclist])


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print ("Usage: python step1_links2points.py <aoi> <tracking_links> <tracking_points> ")
        print ("Example: python step1_links2points.py ./data/aoi.shp ./data/tracking_links.shp ./data/tracking_points.shp")
    else:
        aoifilename,infilename,outfilename = sys.argv[1],sys.argv[2],sys.argv[3]
        process(aoifilename,infilename,outfilename)