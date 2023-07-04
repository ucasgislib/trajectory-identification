#-*- coding:utf-8 -*-

import sys
import ogr,osr
import time
import math
import numpy as np
from rtree import index

from utils import ARCVIEW_SHAPE

def create_index(reclist):
    tree = index.Index()
    i = 0
    while i < len(reclist):
        x1,x2,y1,y2 = reclist[i]["x1"],reclist[i]["x2"],reclist[i]["y1"],reclist[i]["y2"]
        tree.insert(i,(min(x1,x2),min(y1,y2),max(x1,x2),max(y1,y2)))
        i += 1
    return tree

def cal_onsite_heading(px,py,azm,reclist,tree,hw=35):
    xmin,ymin,xmax,ymax = px-hw,py-hw,px+hw,py+hw
    idx = list(tree.intersection((xmin,ymin,xmax,ymax)))
    azms = []
    for i in idx:
        azm_ = reclist[i]["lazm"]
        d = math.degrees(max(azm_,azm)-min(azm_,azm))
        if (d >= 0 and d < 90) or (d >270 and d<=360):
            azms.append(math.degrees(azm_))

    mina,maxa = min(azms),max(azms)
    if (maxa-mina) < 180:
        pazm = float(np.mean(np.array(azms)))
    else:
        for i in range(len(azms)):
            if azms[i] >= 0 and azms[i]<180:
                azms[i] += 360
        pazm = float(np.mean(np.array(azms)))%360

    return math.radians(pazm)

def process(infilename,outfilename,buff=35):
    shp_drv = ARCVIEW_SHAPE()
    
    # tracking links
    spatialref,geomtype,geomlist,fieldlist,reclist = shp_drv.read_shp(infilename)
    tree = create_index(reclist)

    #calculate onsite-heading 
    cp = 0
    for rec in reclist:
        x1,y1,x2,y2 = rec["x1"],rec["y1"],rec["x2"],rec["y2"]
        pazm1 = cal_onsite_heading(x1,y1,rec["lazm"],reclist,tree,hw=buff)
        pazm2 = cal_onsite_heading(x2,y2,rec["lazm"],reclist,tree,hw=buff)
        rec["pazm1"] = pazm1
        rec["pazm2"] = pazm2
        cp+=1
        if cp%1000==0:
            print("%d of %d"%(cp,len(reclist)))

    #output link file, endpoint-onsite-heading added
    fieldlist.append({'width': 20, 'decimal': 4, 'type': ogr.OFTReal,'name': 'pazm1'}) 
    fieldlist.append({'width': 20, 'decimal': 4, 'type': ogr.OFTReal,'name': 'pazm2'})

    shp_drv.write_shp(outfilename,[spatialref,geomtype,geomlist,fieldlist,reclist])

if __name__ == '__main__':

    if len(sys.argv) != 4:
        print ("Usage: python step5_link_endpoint_onsite_heading.py <tracking_links> <onsite_heading> <window>")
        print ("Example: python step5_link_endpoint_onsite_heading.py ./data/tracking_links.shp ./data/tracking_links.shp 35")
    else:
        infilename,outfilename,buff = sys.argv[1],sys.argv[2], int(sys.argv[3])
        # infilename = "./data/tracking_links1.shp"
        # outfilename = "./data/tracking_links3.shp"
        # buff = 35
        process(infilename,outfilename,buff)
