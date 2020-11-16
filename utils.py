#!/usr/bin/env python3
import pandas as pd
from sklearn.datasets import load_svmlight_file
from sklearn.externals.joblib import Memory
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.metrics import precision_recall_curve
from sklearn.metrics import f1_score
from matplotlib import pyplot as plt
from numpy import savetxt
import warnings
import numpy as np
import tensorflow as tf
import sklearn.metrics as sk_m

mem = Memory("./dataset/svm_data")


@mem.cache
def get_data_from_svmlight_file(path):
    data = load_svmlight_file(path)
    return data[0], data[1]


def dataLoading():
    # loading data
    
    labels = pd.read_csv('./dataset/y_train_NetMl_pluslabels.csv')
    
    x =  pd.read_csv('./dataset/x_train_NetMl_pluslabels.csv')
    
    print("Data shape: (%d, %d)" % x.shape)

    return x, labels

def aucPerformance_norm(mse, labels):
    roc_auc = roc_auc_score(labels, mse)
    ap = average_precision_score(labels, mse)
    print("AUC-ROC: %.4f, AUC-PR: %.4f" % (roc_auc, ap))
    return roc_auc, ap

def prec(scores, y_test):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')  
    prec, rec, thr = precision_recall_curve(y_test, scores)
    figura = plt.figure()
    plt.plot(thr, prec[:-1], 'b--', label='precision')
    plt.plot(thr, rec[:-1], 'g--', label = 'recall')
    plt.xlabel('Threshold')
    plt.legend(loc='upper right')
    plt.ylim([0,1])
    figura.savefig('figura.png')
        
    figura2 = plt.figure()
    plt.plot(rec, prec)
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    figura2.savefig('figura2.png')
    
    f1 = 2 * ((prec * rec) / (prec + rec))
    max_prec = prec[np.argmax(f1)]
    max_rec = rec[np.argmax(f1)]
    print('max precision', max_prec)
    print('max recall', max_rec)
    f1 = 2 * ((max_prec * max_rec) / (max_prec + max_rec ))
    print('f1', f1)
    
    return max_prec, max_rec, f1
    

def writeResults(filename, supervision, architecture,epochs,batch_size,nb_batch,losses,final_outlier_Adload,final_outlier_Artemis,final_outlier_BitCoinMiner,final_outlier_CCleaner,final_outlier_Cobalt, final_outlier_Downware, final_outlier_Dridex, final_outlier_Emotet,final_outlier_HTBot, final_outlier_MagicHound, final_outlier_MinerTrojan, final_outlier_PUA, final_outlier_Ramnit, final_outlier_Sality, final_outlier_Tinba, final_outlier_TrickBot, final_outlier_Trickster, final_outlier_TrojanDownloader, final_outlier_Ursnif, final_outlier_WebCompanion, rauc, ap, precision_new, recall_new, f1_new, n_samples_trn,n_outliers,inlier_number,n_noise,train_time,max_precision,max_recall,f_one,path="./results/performanceNetMl.csv"):
    
    csv_file = open(path, 'a')                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              
    row = filename+ "," + str(supervision) + "," + str(architecture) + "," + str(epochs) + "," + str(batch_size) + "," + str(nb_batch) + "," + str(losses) + "," + str(final_outlier_Adload) + "," + str(final_outlier_Artemis) + "," + str(final_outlier_BitCoinMiner) + "," + str(final_outlier_CCleaner) + "," + str(final_outlier_Cobalt) + "," + str(final_outlier_Downware) + "," + str(final_outlier_Dridex) + "," + str(final_outlier_Emotet) + "," + str(final_outlier_HTBot) + "," + str(final_outlier_MagicHound) + "," + str(final_outlier_MinerTrojan) + "," + str(final_outlier_PUA) + "," + str(final_outlier_Ramnit) + "," + str(final_outlier_Sality) + "," + str(final_outlier_Tinba) + "," + str(final_outlier_TrickBot) + "," +  str(final_outlier_Trickster) + "," + str(final_outlier_TrojanDownloader) + "," + str(final_outlier_Ursnif) + "," + str(final_outlier_WebCompanion) + "," + str(rauc) + "," + str(ap) + "," + str(precision_new) + "," + str(recall_new) + "," + str(f1_new) + "," + str(n_samples_trn) + "," + str(n_outliers) + "," + str(inlier_number) + "," + str(n_noise) + "," + str(train_time) + ","+ str(max_precision) + "," + str(max_recall) + "," + str(f_one) + "\n"
    csv_file.write(row)
    
