#-*- coding:utf-8 -*-

import sys
import gdal,ogr,osr
import time
import math
import numpy as np
# import matplotlib.pyplot as plt
# from pylab import *  
from rtree import index

from utils import ARCVIEW_SHAPE

class INFORMATION_ENTROPY(object):
    def __init__(self):
        self.shp_drv = ARCVIEW_SHAPE()

    def create_linkindex(self,reclist):
        tree = index.Index()
        i = 0
        lazm = []
        while i < len(reclist):
            x1,x2,y1,y2 = reclist[i]["x1"],reclist[i]["x2"],reclist[i]["y1"],reclist[i]["y2"]
            tree.insert(i,(min(x1,x2),min(y1,y2),max(x1,x2),max(y1,y2)))
            lazm.append(reclist[i]["lazm"])
            i += 1
        return np.array(lazm),tree

    def create_pointindex(self,reclist):
        tree = index.Index()
        i = 0
        while i < len(reclist):
            x,y = reclist[i]["x"],reclist[i]["y"]
            tree.insert(i,(x,y,x,y))
            i += 1
        return tree

    def cal_azm_(self,x1array,y1array,x2array,y2array):
        dy = y2array - y1array
        dx = x2array - x1array
        azm = np.zeros(len(x1array))
        azm = np.where(dy>0,np.arctan(dx/dy),azm)
        azm = np.where(azm<0,azm+2*math.pi,azm)
        azm = np.where(dy<0,np.arctan(dx/dy) + math.pi,azm)
        px1 = np.where(dy==0,1,0)*np.where(dx>0,1,0)
        px2 = np.where(dy==0,1,0)*np.where(dx<=0,1,0)
        azm = np.where(px1==1,math.pi/2,azm)
        azm = np.where(px2==1,math.pi*3/2,azm)
        return azm

    def cal_azm(self,px,py,lazms,tree,hw=35):
        xmin,ymin,xmax,ymax = px-hw,py-hw,px+hw,py+hw
        idx = list(tree.intersection((xmin,ymin,xmax,ymax)))
        selected = lazms[idx]
        return selected

    def cal_entropy_(self,lazm):
        azm = lazm/math.pi * 180
        azm = np.where(azm>=180,azm-180,azm)
        azm = np.where(azm>=157.5,azm-180,azm)

        #statistics on azm (4 sectors,each 45 degree)
        drct = ((azm+22.5)/45.0).astype(int)*45
        val = []
        for k in range(0,180,45):
            v = len(np.where(drct==k)[0])
            val.append(v)  
        val = np.array(val)
        ph = 1.0*val/np.sum(val)

        # calculate entropy
        pb = 1.0*val/np.sum(val)
        w = 0.95
        pw=np.zeros(4)
        pw[(np.argmax(pb)+0)%4]=1+w
        pw[(np.argmax(pb)+2)%4]=1+w
        pw[(np.argmax(pb)+1)%4]=1-w
        pw[(np.argmax(pb)+3)%4]=1-w
        pw=pw[np.where(pb>0)]
        pb=pb[np.where(pb>0)]
        entropy = np.sum(-pw*pb*np.log(pb)/np.log(2))

        return entropy,list(ph)

    def cal_entropy(self,pnts,lazms,link_tree,point_tree,hw=35):
        entropy_pool = []
        pnts_num = len(pnts)
        i = 0
        while i < pnts_num:
            px,py,m = pnts[i,0],pnts[i,1],pnts[i,2]
            if m == 0:
                h = -1
                ln,pn = 0,0
                ph=[0,0,0,0]
            else:
                xmin,ymin,xmax,ymax = px-hw,py-hw,px+hw,py+hw
                idx = list(point_tree.intersection((xmin,ymin,xmax,ymax)))  
                pn = len(idx)# pn is the number of points
                lazm = self.cal_azm(px,py,lazms,link_tree,hw=hw)
                ln = lazm.shape[0] # ln is the number of links
                h,ph = self.cal_entropy_(lazm) #entropy(h) is calculated by n neighbour links
            entropy_pool.append([h,ln,pn,ph[0],ph[1],ph[2],ph[3]])
            i+=1
            if i%1000 == 0:
                print("%d of %d"%(i,pnts_num))

            # if i == 100000:
            #     break

        return entropy_pool

    def plot_entropy_hist(self,entropy):
        mpl.rcParams['font.sans-serif'] = ['Arial']
        font2 = {'family' : 'Times New Roman','size' : 18}
        fig = plt.figure(figsize=(6,6))
        ax = fig.add_subplot(1,1,1)
        ax.hist(entropy,15,color="#B8860B",normed=1,label=u'Histogram of point-entropy')
        ax.set_ylabel(u'Frequency(%)',font2)
        ax.set_xlabel(u'Information entropy',font2)
        ax.set_xticks([0,0.3,0.6,0.9,1.2,1.5,1.8])
        ax.set_yticks([0,1,2])
        ax.legend(prop=font2,loc='upper left')
        plt.tick_params(labelsize=14)
        # fig.savefig('entropy.png',dpi=300)
        plt.show()

    def run(self,infilename,linkfilename,outfilename,buff=35,start=0,end=-1):
        #tracking links
        spatialref,geomtype,geomlist,fieldlist,reclist = self.shp_drv.read_shp(linkfilename)

        #index tree and azimuth array for tracking links
        lazm,link_tree = self.create_linkindex(reclist)
        glist = [ogr.CreateGeometryFromWkt(geom) for geom in geomlist]   

        #tracking points
        spatialref,geomtype,geomlist,fieldlist,reclist = self.shp_drv.read_shp(infilename)
        point_tree = self.create_pointindex(reclist)

        if end == -1:
            reclist = reclist[start:]
            geomlist = geomlist[start:]    
        else:
            reclist = reclist[start:end]
            geomlist = geomlist[start:end]

        points = []
        for rec in reclist:
            pid,tid,x,y,t,m =  rec["pid"],rec["tid"],rec["x"],rec["y"],rec["t"],rec["m"]
            points.append([x,y,m])
        points = np.array(points)

        #information entropy for tracking points
        entropy = self.cal_entropy(points,lazm,link_tree,point_tree,hw=buff)
        entropy = np.array(entropy)

        i = 0
        while i < len(entropy):
            #
            reclist[i]["entropy"] = float(entropy[i,0])
            reclist[i]["entropy_ln"] = int(entropy[i,1])
            reclist[i]["entropy_pn"] = int(entropy[i,2])
            #
            reclist[i]["ph0"] = float(entropy[i,3])
            reclist[i]["ph1"] = float(entropy[i,4])
            reclist[i]["ph2"] = float(entropy[i,5])
            reclist[i]["ph3"] = float(entropy[i,6])
            #
            i += 1

        
        #entropy shape organization(two new fields added to input tracking points)
        fieldlist.append({'width': 20, 'decimal': 6, 'type': ogr.OFTReal, 'name': 'entropy'})
        fieldlist.append({'width': 20, 'type': ogr.OFTInteger, 'name': 'entropy_ln'})
        fieldlist.append({'width': 20, 'type': ogr.OFTInteger, 'name': 'entropy_pn'})
        fieldlist.append({'width': 20, 'decimal': 6, 'type': ogr.OFTReal, 'name': 'ph0'})
        fieldlist.append({'width': 20, 'decimal': 6, 'type': ogr.OFTReal, 'name': 'ph1'})
        fieldlist.append({'width': 20, 'decimal': 6, 'type': ogr.OFTReal, 'name': 'ph2'})
        fieldlist.append({'width': 20, 'decimal': 6, 'type': ogr.OFTReal, 'name': 'ph3'})

        data = [spatialref,geomtype,geomlist,fieldlist,reclist]
        self.shp_drv.write_shp(outfilename,data)
        
        #histogram of tracking points entropy
        # entropy_ = [v[0] for v in entropy if v[0]>=0]
        # self.plot_entropy_hist(entropy_)


if __name__ == '__main__':

    if len(sys.argv) != 7:
        print ("Usage: python step2_point_entropy.py <tracking_points> <tracking_links> <entropy> <window>")
        print ("Example: python step2_point_entropy.py ./data/tracking_points.shp ./data/tracking_links.shp ./data/tracking_points.shp 35")
    else:
        test = INFORMATION_ENTROPY()
        infilename,linkfilename,outfilename,buff,start,end = sys.argv[1],sys.argv[2],sys.argv[3],int(sys.argv[4]),int(sys.argv[5]),int(sys.argv[6])
        test.run(infilename,linkfilename,outfilename,buff=buff,start=start,end=end)