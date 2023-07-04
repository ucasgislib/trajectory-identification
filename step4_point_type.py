#-*- coding:utf-8 -*-

import sys
import ogr
import time
import math
import numpy as np
from rtree import index
from sklearn.model_selection import train_test_split  
from sklearn.linear_model import LogisticRegression  
from sklearn import tree
from sklearn.tree import DecisionTreeClassifier, plot_tree

from sklearn.metrics import roc_curve, auc
import os     
import pydotplus
from utils import ARCVIEW_SHAPE

class POINT_CLASSFICATION(object):
    def __init__(self):
        self.shp_drv = ARCVIEW_SHAPE()

    def __del__(self):
        pass
        
    def classification(self,train_points,entropy_data,c=0.00125,penalty='l2',method = "lg"):
        np.random.shuffle(train_points)
        # data = train_points[:,0].reshape(-1,1)
        # print(data)
        # label = train_points[:,1]
        # label = label.astype(np.int)
        # print(label)
        # 
        data = [[r[0],r[1]] for r in train_points]
        label = [[r[2]] for r in train_points]

        train_data,test_data, train_label, test_label = train_test_split(data,label,test_size=0.8, random_state=0)
        pred_data = [[r[0],r[1]] for r in entropy_data]
        
        if method == "lg":
            #
            model = LogisticRegression(C=c, penalty=penalty, tol=0.01, solver='saga')
            if penalty == "elasticnet":
                clf = LogisticRegression(C=c, penalty=penalty, l1_ratio=0.4,tol=0.01, solver='saga') 
            if penalty == "none":
                clf = LogisticRegression() 
            model.fit(data, label)

        if method == "tree":
            # clf = tree.DecisionTreeClassifier(criterion='entropy',max_depth= 3,min_samples_leaf = 20,  splitter='best')
            model = tree.DecisionTreeClassifier()
            model.fit(data, label)
            
            # with open("iris.dot", 'w') as f:
            #     f = tree.export_graphviz(model, out_file=f)
            
            # os.environ["PATH"] += os.pathsep + 'C:/Program Files (x86)/Graphviz2.38/bin/'
            
            # dot_data = tree.export_graphviz(model)
            # graph = pydotplus.graph_from_dot_data(dot_data)
            # # 保存图像到pdf文件
            # graph.write_pdf("iris.pdf")


        if method == "forest":
            from sklearn.ensemble import RandomForestClassifier
            # Create the model with 100 trees
            model = RandomForestClassifier()
            # Fit on training data
            model.fit(data, label)


            # from sklearn.ensemble import ExtraTreesClassifier

            # # Create the model with 100 trees
            # model = ExtraTreesClassifier()
            # # Fit on training data
            # model.fit(train_data, train_label)


        # Actual class predictions
        pred = model.predict(pred_data)
        # # Probabilities for each class
        # rf_probs = model.predict_proba(test_data)[:, 1]

        # from sklearn.metrics import roc_auc_score

        # # Calculate roc auc
        # roc_value = roc_auc_score(test_label, rf_probs)


        # import matplotlib.pyplot as plt
        # prob_predict_y_validation = model.predict_proba(test_data)#给出带有概率值的结果，每个点所有label的概率和为1
        # predictions_validation = prob_predict_y_validation[:, 1]
        # fpr, tpr, _ = roc_curve(test_label, predictions_validation)
        #     #
        # roc_auc = auc(fpr, tpr)
        # plt.title('ROC Validation')
        # plt.plot(fpr, tpr, 'b', label='AUC = %0.2f' % roc_auc)
        # plt.legend(loc='lower right')
        # plt.plot([0, 1], [0, 1], 'r--')
        # plt.xlim([0, 1])
        # plt.ylim([0, 1])
        # plt.ylabel('True Positive Rate')
        # plt.xlabel('False Positive Rate')
        # plt.show()

        return pred

    def run(self,infilename,samplefilename,outfilename,c=0.00125,penalty='l2',t=0.05,method = "lg"):
        #sample points for model training
        spatialref,geomtype,geomlist,fieldlist,reclist = self.shp_drv.read_shp(samplefilename)
        train_points = []
        for rec in reclist:
            # print(rec)
            entropy,grad,label = rec["entropy"],rec["grad"],rec["label"]
            if grad <-1:
                grad= -1
            train_points.append([entropy,grad,label])
        train_points = np.array(train_points)

        #tracking points to be classified
        spatialref,geomtype,geomlist,fieldlist,reclist = self.shp_drv.read_shp(infilename)
        entropy_ln = [rec["entropy_ln"] for rec in reclist if rec["m"]==1]
        entropy_ln.sort()
        threshold = entropy_ln[int(t*len(entropy_ln))] #1st percentile 

        entropy_pn = [rec["entropy_pn"] for rec in reclist if rec["m"]==1]
        entropy_pn.sort()
        pn_threshold = entropy_pn[int(t*len(entropy_pn))] #1st percentile 

        #points inside aoi with entropy calculated
        entropy_data = []
        cp = 0
        for rec in reclist:
            entropy,entropy_ln,entropy_pn,m,grad = rec['entropy'],rec['entropy_ln'],rec['entropy_pn'],rec['m'],rec["grad"]
            if grad <-1:
                grad= -1
            if entropy_ln>=threshold and m == 1 and entropy_pn>=pn_threshold:
                entropy_data.append([entropy,grad,cp])
            cp+=1
        entropy_data = np.array(entropy_data)
        print(len(entropy_data))
        entropy_pred = self.classification(train_points,entropy_data,c=c,penalty=penalty,method = method)
        print(1 in entropy_pred,len(entropy_pred),len(reclist))
        cp = 0
        while cp<len(entropy_pred):
            reclist[int(entropy_data[cp,2])]["label"] = int(entropy_pred[cp])
            cp+=1

        #points inside aoi but entropy un-calculated
        for rec in reclist:
            if rec["entropy_ln"] < threshold or rec["entropy_pn"] < pn_threshold:
                rec["label"] = -1
                
        #points outside aoi 
        for rec in reclist:
            if rec["m"] == 0:
                rec["label"] = -2

        #label shape organization
        fieldlist.append({'width': 20, 'type': ogr.OFTInteger, 'name': 'label'})
        self.shp_drv.write_shp(outfilename,[spatialref,geomtype,geomlist,fieldlist,reclist])
        
if __name__ == '__main__':
    if len(sys.argv) != 8:
        print ("Usage: python step3_point_type.py <entropy> <training> <labeled>")
        print ("Example: python step3_point_type.py  ./data/tracking_points.shp ./data/sample_points.shp ./data/tracking_points.shp")
    else:
        test = POINT_CLASSFICATION()
        infilename,samplefilename,outfilename,c,p,t = sys.argv[1],sys.argv[2],sys.argv[3],float(sys.argv[4]),sys.argv[5],float(sys.argv[6])
        method = sys.argv[7]
        # infilename="./data/tracking_points1.shp" 
        # samplefilename="./data/sample_points.shp" 
        # outfilename="./data/tracking_points2.shp"
        test.run(infilename,samplefilename,outfilename,c,p,t,method)