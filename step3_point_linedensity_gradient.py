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

    def cal_linedensity_(self,px,py,glist,tree,hw=35):
        xmin,ymin,xmax,ymax = px-hw,py-hw,px+hw,py+hw
        idx = list(tree.intersection((xmin,ymin,xmax,ymax)))
        
        dist = 0
        window = ogr.CreateGeometryFromWkt("POLYGON((%f %f,%f %f,%f %f,%f %f,%f %f))"%(xmin,ymin,xmin,ymax,xmax,ymax,xmax,ymin,xmin,ymin))
        for i in idx:
            g = glist[i]
            s = g.Intersection(window)
            # print(s.Length())
            dist += s.Length()
        ld = dist/(4*hw**2)

        return ld,len(idx)

    def cal_linedensity(self,points,glist,tree,hw=35):
        ld_pool = [] 
        pnts_num = points.shape[0]
        i = 0
        coeff = 2.5
        while i<pnts_num:
            px0,py0 = points[i,0],points[i,1]
            px1,py1 = px0+2*hw,py0
            px2,py2 = px0+2*hw,py0-2*hw
            px3,py3 = px0,py0-2*hw
            px4,py4 = px0-2*hw,py0-2*hw
            px5,py5 = px0-2*hw,py0
            px6,py6 = px0-2*hw,py0+2*hw
            px7,py7 = px0,py0+2*hw
            px8,py8 = px0+2*hw,py0+2*hw

            ld0,ln0 = self.cal_linedensity_(px0,py0,glist,tree,hw=hw)
            ld1,ln1 = self.cal_linedensity_(px1,py1,glist,tree,hw=hw)
            ld2,ln2 = self.cal_linedensity_(px2,py2,glist,tree,hw=hw)
            ld3,ln3 = self.cal_linedensity_(px3,py3,glist,tree,hw=hw)
            ld4,ln4 = self.cal_linedensity_(px4,py4,glist,tree,hw=hw)
            ld5,ln5 = self.cal_linedensity_(px5,py5,glist,tree,hw=hw)
            ld6,ln6 = self.cal_linedensity_(px6,py6,glist,tree,hw=hw)
            ld7,ln7 = self.cal_linedensity_(px7,py7,glist,tree,hw=hw)
            ld8,ln8 = self.cal_linedensity_(px8,py8,glist,tree,hw=hw)

            # ld = [ld1,ld2,ld3,ld4,ld5,ld6,ld7,ld8]
            # ld.sort()
            # ld_ = ld[-2]
            # if ld_ == 0:
            #     ld_ = ld[-1]
            # grad = (ld0-ld_)/ld0
            grad = (ld0-max([ld1,ld2,ld3,ld4,ld5,ld6,ld7,ld8]))/ld0
            
            # grad = abs(ld0-(ld1*coeff))/max(ld0,(ld1*coeff))
            # ln = max(ln0,ln1)
            # print(i,ld0,ln0,ld1,ln1)
            ld_pool.append([grad,ld0,ld1,ld2,ld3,ld4,ld5,ld6,ld7,ld8,ln0,ln1,ln2,ln3,ln4,ln5,ln6,ln7,ln8])
            i+=1
            if i%1000 == 0:
                print("%d of %d"%(i,pnts_num))

            # if i == 100000:
            #     break


        return ld_pool

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

        #density grad for tracking points
        linedensity = self.cal_linedensity(points,glist,link_tree,hw=buff)
        linedensity = np.array(linedensity)

        i = 0
        while i < len(linedensity):
            #
            reclist[i]["grad"] = float(linedensity[i,0])
            reclist[i]["ld0"] = float(linedensity[i,1])
            reclist[i]["ld1"] = float(linedensity[i,2])
            reclist[i]["ld2"] = float(linedensity[i,3])
            reclist[i]["ld3"] = float(linedensity[i,4])
            reclist[i]["ld4"] = float(linedensity[i,5])
            reclist[i]["ld5"] = float(linedensity[i,6])
            reclist[i]["ld6"] = float(linedensity[i,7])
            reclist[i]["ld7"] = float(linedensity[i,8])
            reclist[i]["ld8"] = float(linedensity[i,9])
            #
            i += 1

        
        #entropy shape organization(two new fields added to input tracking points)
        fieldlist.append({'width': 20, 'decimal': 6, 'type': ogr.OFTReal, 'name': 'grad'})
        fieldlist.append({'width': 20, 'decimal': 6, 'type': ogr.OFTReal, 'name': 'ld0'})
        fieldlist.append({'width': 20, 'decimal': 6, 'type': ogr.OFTReal, 'name': 'ld1'})
        fieldlist.append({'width': 20, 'decimal': 6, 'type': ogr.OFTReal, 'name': 'ld2'})
        fieldlist.append({'width': 20, 'decimal': 6, 'type': ogr.OFTReal, 'name': 'ld3'})
        fieldlist.append({'width': 20, 'decimal': 6, 'type': ogr.OFTReal, 'name': 'ld4'})
        fieldlist.append({'width': 20, 'decimal': 6, 'type': ogr.OFTReal, 'name': 'ld5'})
        fieldlist.append({'width': 20, 'decimal': 6, 'type': ogr.OFTReal, 'name': 'ld6'})
        fieldlist.append({'width': 20, 'decimal': 6, 'type': ogr.OFTReal, 'name': 'ld7'})
        fieldlist.append({'width': 20, 'decimal': 6, 'type': ogr.OFTReal, 'name': 'ld8'})

        
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