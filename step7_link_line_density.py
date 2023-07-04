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

def cal_line_density(px,py,glist,tree,hw=35):
    xmin,ymin,xmax,ymax = px-hw,py-hw,px+hw,py+hw
    idx = list(tree.intersection((xmin,ymin,xmax,ymax)))
    
    dist = 0
    window = ogr.CreateGeometryFromWkt("POLYGON((%f %f,%f %f,%f %f,%f %f,%f %f))"%(xmin,ymin,xmin,ymax,xmax,ymax,xmax,ymin,xmin,ymin))
    for i in idx:
        g = glist[i]
        s = g.Intersection(window)
        dist += s.Length()
    ld = dist/(4*hw**2)

    # ld = len(idx)/(2*hw)

    return ld

def process(infilename,outfilename,buff=35):
    shp_drv = ARCVIEW_SHAPE()
    
    # tracking links
    spatialref,geomtype,geomlist,fieldlist,reclist = shp_drv.read_shp(infilename)
    glist = [ogr.CreateGeometryFromWkt(geom) for geom in geomlist]    
    tree = create_index(reclist)

    #calculate line-density 
    cp = 0
    for rec in reclist:
        x1,y1,x2,y2 = rec["x1"],rec["y1"],rec["x2"],rec["y2"]
        xm,ym = (x1+x2)/2,(y1+y2)/2
        pkd1 = cal_line_density(x1,y1,glist,tree,hw=buff)
        pkd2 = cal_line_density(x2,y2,glist,tree,hw=buff)
        lkd = cal_line_density(xm,ym,glist,tree,hw=buff)
        rec["pkd1"] = pkd1
        rec["pkd2"] = pkd2
        rec["lkd"] = lkd
        cp+=1
        if cp%1000==0:
            print("%d of %d"%(cp,len(reclist)))

    #output link file, endpoint-onsite-heading added
    fieldlist.append({'width': 20, 'decimal': 4, 'type': ogr.OFTReal,'name': 'lkd'}) 
    fieldlist.append({'width': 20, 'decimal': 4, 'type': ogr.OFTReal,'name': 'pkd1'}) 
    fieldlist.append({'width': 20, 'decimal': 4, 'type': ogr.OFTReal,'name': 'pkd2'})

    shp_drv.write_shp(outfilename,[spatialref,geomtype,geomlist,fieldlist,reclist])

if __name__ == '__main__':

    if len(sys.argv) != 4:
        print ("Usage: python step6_link_line_density.py <tracking_links> <line_density> <window>")
        print ("Example: python step6_link_line_density.py ./data/tracking_links.shp ./data/tracking_links.shp 35")
    else:
        infilename,outfilename,buff = sys.argv[1],sys.argv[2], int(sys.argv[3])
        # infilename = "./data/tracking_links3.shp"
        # outfilename = "./data/tracking_links4.shp"
        # buff = 35
        process(infilename,outfilename,buff)
