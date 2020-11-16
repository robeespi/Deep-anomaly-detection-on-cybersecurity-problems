                        
import os
import numpy as np

np.random.seed(42)
import tensorflow as tf
tf.config.experimental_run_functions_eagerly(True)

tf.random.set_seed(42)

sess = tf.compat.v1.initialize_all_variables()

from tensorflow.keras import regularizers
from tensorflow.keras import backend as K
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense, Dropout
from tensorflow.keras.optimizers import RMSprop
from tensorflow.keras.callbacks import ModelCheckpoint

import argparse
import numpy as np
import sys
from scipy.sparse import vstack, csc_matrix
from utils import dataLoading, aucPerformance_norm, writeResults, get_data_from_svmlight_file
from sklearn.model_selection import train_test_split
from numpy import savetxt, save
from sklearn.metrics import precision_recall_curve
from sklearn.metrics import f1_score
from matplotlib import pyplot as plt
from sklearn.metrics import precision_score, recall_score
from keras.models import load_model
import warnings
warnings.filterwarnings('ignore')


import time

MAX_INT = np.iinfo(np.int32).max
data_format = 0


def dev_network_d(input_shape):
    '''
    network architecture with three hidden layer
    '''
    #Original
    x_input = Input(shape=input_shape)
    intermediate = Dense(3000, activation='relu',
                kernel_regularizer=regularizers.l2(0.01), name = 'hl1')(x_input)
    intermediate = Dropout(0.5)(intermediate)
    intermediate = Dense(750, activation='relu',
                kernel_regularizer=regularizers.l2(0.01), name = 'hl2')(intermediate)
    intermediate = Dropout(0.5)(intermediate)
    intermediate = Dense(60, activation='relu',
                kernel_regularizer=regularizers.l2(0.01), name = 'hl3')(intermediate)
    intermediate = Dropout(0.5)(intermediate)
    intermediate = Dense(1, activation='linear', name = 'score')(intermediate)
     
    #return Model(x_input, intermediate)
    return Model(x_input, intermediate)

def dev_network_s(input_shape):
    '''
    network architecture with one hidden layer
    '''
    x_input = Input(shape=input_shape)
    intermediate = Dense(25, activation='relu', 
                kernel_regularizer=regularizers.l2(0.01), name = 'hl1')(x_input)
    intermediate = Dropout(0.5)(intermediate)
    intermediate = Dense(5, activation='relu', 
                kernel_regularizer=regularizers.l2(0.01), name = 'hl2')(intermediate)
    intermediate = Dropout(0.5)(intermediate)
    intermediate = Dense(1, activation='linear',  name = 'score')(intermediate)
    #intermediate = Dropout(0.5)(intermediate)
    return Model(x_input, intermediate)

def deviation_loss(y_true, y_pred):
    '''
    z-score-based deviation loss
    '''
    y_true = tf.cast(y_true, tf.float32)
    y_pred = tf.cast(y_pred, tf.float32)
    confidence_margin = 5.
    ref = K.variable(np.random.normal(loc=0., scale=1.0, size=5000), dtype='float32')
    dev = (y_pred - K.mean(ref)) / K.std(ref)
    inlier_loss = K.abs(dev)
    outlier_loss = K.abs(K.maximum(confidence_margin - dev, 0.))
    return K.mean((1 - y_true) * inlier_loss + y_true  * outlier_loss)


def deviation_network(input_shape, network_depth):
    '''
    construct the deviation network-based detection model
    '''

    if network_depth == 4:
        model = dev_network_d(input_shape)
    elif network_depth == 2:
        model = dev_network_s(input_shape)
    else:
        sys.exit("The network depth is not set properly")
    rms = RMSprop(clipnorm=1.)
    #model.compile(loss='binary_crossentropy', optimizer=rms)
    model.compile(loss=deviation_loss, optimizer=rms)

    return model


def batch_generator_sup(x,outlier_indices,inlier_indices,outlier_Adload_indices, outlier_Artemis_indices, outlier_BitCoinMiner_indices, outlier_CCleaner_indices, outlier_Cobalt_indices, outlier_Downware_indices, outlier_Dridex_indices, outlier_Emotet_indices, outlier_HTBot_indices, outlier_MagicHound_indices, outlier_MinerTrojan_indices, outlier_PUA_indices, outlier_Ramnit_indices, outlier_Sality_indices, outlier_Tinba_indices, outlier_TrickBot_indices, outlier_Trickster_indices, outlier_TrojanDownloader_indices, outlier_Ursnif_indices, outlier_WebCompanion_indices, opt, batch_size, nb_batch, rng):
    """batch generator
    """
    rng = np.random.RandomState(rng.randint(MAX_INT, size=1))
    counter = 0
    while 1:
        if data_format == 0:
            """batch generator weakly supervised case knowing 10 classes
            """
            ref, training_labels = input_batch_generation_weaklysuptenclass_an_nn(x, outlier_indices, inlier_indices, outlier_Adload_indices, outlier_Artemis_indices, outlier_BitCoinMiner_indices, outlier_CCleaner_indices, outlier_Cobalt_indices, outlier_Downware_indices, outlier_Dridex_indices, outlier_Emotet_indices, outlier_HTBot_indices, outlier_MagicHound_indices, outlier_MinerTrojan_indices, outlier_PUA_indices, outlier_Ramnit_indices, outlier_Sality_indices, outlier_Tinba_indices, outlier_TrickBot_indices, outlier_Trickster_indices, outlier_TrojanDownloader_indices, outlier_Ursnif_indices, outlier_WebCompanion_indices, opt, batch_size, rng)   
        else:
            ref, training_labels = input_batch_generation_sup_sparse(x, outlier_indices, inlier_indices, batch_size, rng)
        counter += 1
        yield (ref, training_labels)
        if (counter > nb_batch):
            counter = 0

def poolref(training_labels, training_labels2, training_labels3,option,x_train, n_inliers, n_outliers, outlier_indices, inlier_indices, n_outliers_Adload, n_outliers_Artemis, n_outliers_BitCoinMiner,n_outliers_CCleaner,n_outliers_Cobalt,n_outliers_Downware,n_outliers_Dridex,n_outliers_Emotet,n_outliers_HTBot,n_outliers_MagicHound,n_outliers_MinerTrojan, n_outliers_PUA,n_outliers_Ramnit,n_outliers_Sality,n_outliers_Tinba,n_outliers_TrickBot,n_outliers_Trickster,n_outliers_TrojanDownloader,n_outliers_Ursnif,n_outliers_WebCompanion,outlier_Adload_indices, outlier_Artemis_indices, outlier_BitCoinMiner_indices,outlier_CCleaner_indices, outlier_Cobalt_indices, outlier_Downware_indices,outlier_Dridex_indices, outlier_Emotet_indices, outlier_HTBot_indices,outlier_MagicHound_indices, outlier_MinerTrojan_indices, outlier_PUA_indices,outlier_Ramnit_indices, outlier_Sality_indices, outlier_Tinba_indices,outlier_TrickBot_indices, outlier_Trickster_indices, outlier_TrojanDownloader_indices,outlier_Ursnif_indices,outlier_WebCompanion_indices,batch_size,rng):
    
    if(option==1): 
        sid = rng.choice(n_outliers_Adload,1) 
        sid2 = rng.choice(n_inliers, 1)
        ref = x_train[outlier_Adload_indices[sid]]
        ref2 = x_train[inlier_indices[sid2]]
        training_labels += [1] 
        training_labels2 += [0]
        training_labels3 += [0] 
                
    elif(option==2):
        #print('Artemis-normal')
        sid = rng.choice(n_outliers_Artemis,1) 
        sid2 = rng.choice(n_inliers, 1)
        ref = x_train[outlier_Artemis_indices[sid]]
        ref2 = x_train[inlier_indices[sid2]]
        training_labels += [1] 
        training_labels2 += [0]
        training_labels3 += [0] 
                
    elif(option==3):
        #print('BitCoinMiner-normal')
        sid = rng.choice(n_outliers_BitCoinMiner,1) 
        sid2 = rng.choice(n_inliers, 1)
        ref = x_train[outlier_BitCoinMiner_indices[sid]]
        ref2 = x_train[inlier_indices[sid2]]
        training_labels += [1] 
        training_labels2 += [0]
        training_labels3 += [0] 
    
    elif(option==4):
        #print('CCleaner-normal')
        sid = rng.choice(n_outliers_CCleaner,1) 
        sid2 = rng.choice(n_inliers, 1)
        ref = x_train[outlier_CCleaner_indices[sid]]
        ref2 = x_train[inlier_indices[sid2]]
        training_labels += [1] 
        training_labels2 += [0] 
        training_labels3 += [0] 
    
    elif(option==5):
        #print('Cobalt-normal')
        sid = rng.choice(n_outliers_Cobalt,1)  
        sid2 = rng.choice(n_inliers, 1) 
        ref = x_train[outlier_Cobalt_indices[sid]]
        ref2 = x_train[inlier_indices[sid2]]
        training_labels += [1] 
        training_labels2 += [0]
        training_labels3 += [0]
        
    elif(option==6):
         #print('Downware-normal')
        sid = rng.choice(n_outliers_Downware,1) 
        sid2 = rng.choice(n_inliers, 1) 
        ref = x_train[outlier_Downware_indices[sid]]
        ref2 = x_train[inlier_indices[sid2]]
        training_labels += [1] 
        training_labels2 += [0]
        training_labels3 += [0]
        
    elif(option==7):
         #print('Dridex-normal')
        sid = rng.choice(n_outliers_Dridex,1) 
        sid2 = rng.choice(n_inliers, 1) 
        ref = x_train[outlier_Dridex_indices[sid]]
        ref2 = x_train[inlier_indices[sid2]]
        training_labels += [1] 
        training_labels2 += [0]
        training_labels3 += [0] 
        
    elif(option==8):
        #print('Emotet-normal')
        sid = rng.choice(n_outliers_Emotet,1) 
        sid2 = rng.choice(n_inliers, 1) 
        ref = x_train[outlier_Emotet_indices[sid]]
        ref2 = x_train[inlier_indices[sid2]]
        training_labels += [1] 
        training_labels2 += [0]
        training_labels3 += [0]
        
    elif(option==9):
        #print('HTBot-normal')
        sid = rng.choice(n_outliers_HTBot,1) 
        sid2 = rng.choice(n_inliers, 1)
        ref = x_train[outlier_HTBot_indices[sid]]
        ref2 = x_train[inlier_indices[sid2]]
        training_labels += [1] 
        training_labels2 += [0]
        training_labels3 += [0] 
    
    elif(option==10):
        #print('MagicHound-normal')
        sid = rng.choice(n_outliers_MagicHound,1) 
        sid2 = rng.choice(n_inliers, 1)
        ref = x_train[outlier_MagicHound_indices[sid]]
        ref2 = x_train[inlier_indices[sid2]]
        training_labels += [1] 
        training_labels2 += [0]
        training_labels3 += [0]
        
    elif(option==11):
        #print('MinerTrojan-normal')
        sid = rng.choice(n_outliers_MinerTrojan,1) 
        sid2 = rng.choice(n_inliers, 1)
        ref = x_train[outlier_MinerTrojan_indices[sid]]
        ref2 = x_train[inlier_indices[sid2]]
        training_labels += [1] 
        training_labels2 += [0]
        training_labels3 += [0] 
         
    elif(option==12):
        #print('PUA-normal')
        sid = rng.choice(n_outliers_PUA,1) 
        sid2 = rng.choice(n_inliers, 1)
        ref = x_train[outlier_PUA_indices[sid]]
        ref2 = x_train[inlier_indices[sid2]]
        training_labels += [1] 
        training_labels2 += [0] 
        training_labels3 += [0]
        
    elif(option==13):
         #print('Ramnit-normal')
        sid = rng.choice(n_outliers_Ramnit,1)  
        sid2 = rng.choice(n_inliers, 1) 
        ref = x_train[outlier_Ramnit_indices[sid]]
        ref2 = x_train[inlier_indices[sid2]]
        training_labels += [1] 
        training_labels2 += [0]
        training_labels3 += [0]
        
    elif(option==14):
        #print('Sality-normal')
        sid = rng.choice(n_outliers_Sality,1) 
        sid2 = rng.choice(n_inliers, 1) 
        ref = x_train[outlier_Sality_indices[sid]]
        ref2 = x_train[inlier_indices[sid2]]
        training_labels += [1] 
        training_labels2 += [0]
        training_labels3 += [0]     
        
    elif(option==15):
        #print('Tinba-normal')
        sid = rng.choice(n_outliers_Tinba,1) 
        sid2 = rng.choice(n_inliers, 1) 
        ref = x_train[outlier_Tinba_indices[sid]]
        ref2 = x_train[inlier_indices[sid2]]
        training_labels += [1] 
        training_labels2 += [0]
        training_labels3 += [0]  
        
    elif(option==16):
        #print('TrickBot-normal')
        sid = rng.choice(n_outliers_TrickBot,1) 
        sid2 = rng.choice(n_inliers, 1) 
        ref = x_train[outlier_TrickBot_indices[sid]]
        ref2 = x_train[inlier_indices[sid2]]
        training_labels += [1] 
        training_labels2 += [0]
        training_labels3 += [0] 
       
    elif(option==17):
        #print('Trickster-normal')
        sid = rng.choice(n_outliers_Trickster,1) 
        sid2 = rng.choice(n_inliers, 1) 
        ref = x_train[outlier_Trickster_indices[sid]]
        ref2 = x_train[inlier_indices[sid2]]
        training_labels += [1] 
        training_labels2 += [0]
        training_labels3 += [0]   
      
    elif(option==18):
        #print('TrojanDownloader-normal')
        sid = rng.choice(n_outliers_TrojanDownloader,1) 
        sid2 = rng.choice(n_inliers, 1) 
        ref = x_train[outlier_TrojanDownloader_indices[sid]]
        ref2 = x_train[inlier_indices[sid2]]
        training_labels += [1] 
        training_labels2 += [0]
        training_labels3 += [0] 
    
    elif(option==19):
        #print('Ursnif-normal')
        sid = rng.choice(n_outliers_Ursnif,1) 
        sid2 = rng.choice(n_inliers, 1) 
        ref = x_train[outlier_Ursnif_indices[sid]]
        ref2 = x_train[inlier_indices[sid2]]
        training_labels += [1] 
        training_labels2 += [0]
        training_labels3 += [0]  
       
    elif(option==20):
        #print('WebCompanion-normal')
        sid = rng.choice(n_outliers_WebCompanion,1) 
        sid2 = rng.choice(n_inliers, 1) 
        ref = x_train[outlier_WebCompanion_indices[sid]]
        ref2 = x_train[inlier_indices[sid2]]
        training_labels += [1] 
        training_labels2 += [0]
        training_labels3 += [0] 
    
    return ref, ref2, training_labels, training_labels2, training_labels3       
    

def input_batch_generation_weaklysuptenclass_an_nn(x_train, outlier_indices, inlier_indices, outlier_Adload_indices, outlier_Artemis_indices, outlier_BitCoinMiner_indices, outlier_CCleaner_indices, outlier_Cobalt_indices, outlier_Downware_indices, outlier_Dridex_indices, outlier_Emotet_indices, outlier_HTBot_indices, outlier_MagicHound_indices, outlier_MinerTrojan_indices, outlier_PUA_indices, outlier_Ramnit_indices, outlier_Sality_indices, outlier_Tinba_indices, outlier_TrickBot_indices, outlier_Trickster_indices, outlier_TrojanDownloader_indices, outlier_Ursnif_indices, outlier_WebCompanion_indices,opt, batch_size, rng):
    '''
    batchs of samples. This is for csv data.
    Alternates between positive and negative pairs.
    '''
    dim = x_train.shape[1]
    ref = np.empty((batch_size, dim))
    ref2 = np.empty((batch_size, dim))
    training_labels = []
    training_labels2 = []
    training_labels3 = []
    
    n_inliers = len(inlier_indices)
    #print('n_inliers len', n_inliers)
    #print('x_train shape', x_train.shape)
    n_outliers = len(outlier_indices)
    #print('n_outliers len', n_outliers)
 
    n_outliers_Adload = len(outlier_Adload_indices)
    #print('anomalies Adload',n_outliers_Adload)
    
    n_outliers_Artemis = len(outlier_Artemis_indices)
    #print('anomalies Artemis',n_outliers_Artemis)
    
    n_outliers_BitCoinMiner = len(outlier_BitCoinMiner_indices)
    #print('anomalies BitCoinMiner',n_outliers_BitCoinMiner)
    
    n_outliers_CCleaner = len(outlier_CCleaner_indices)
    #print('anomalies CCleaner',n_outliers_CCleaner)
    
    n_outliers_Cobalt = len(outlier_Cobalt_indices)
    #print('anomalies Cobalt',n_outliers_Cobalt)
    
    n_outliers_Downware = len(outlier_Downware_indices)
    #print('anomalies Downware',n_outliers_Downware)
    
    n_outliers_Dridex = len(outlier_Dridex_indices)
    #print('anomalies Dridex',n_outliers_Dridex)
    
    n_outliers_Emotet = len(outlier_Emotet_indices)
    #print('anomalies Emotet',n_outliers_Emotet)
    
    n_outliers_HTBot = len(outlier_HTBot_indices)
    #print('anomalies HTBot',n_outliers_HTBot)
    
    n_outliers_MagicHound = len(outlier_MagicHound_indices)
    #print('anomalies MagicHound',n_outliers_MagicHound)
     
    n_outliers_MinerTrojan = len(outlier_MinerTrojan_indices)
    #print('anomalies MinerTrojan',n_outliers_MinerTrojan)
     
    n_outliers_PUA = len(outlier_PUA_indices)
    #print('anomalies PUA',n_outliers_PUA)
    
    n_outliers_Ramnit = len(outlier_Ramnit_indices)
    #print('anomalies Ramnit',n_outliers_Ramnit)
    
    n_outliers_Sality = len(outlier_Sality_indices)
    #print('anomalies Sality',n_outliers_Sality)
    
    n_outliers_Tinba = len(outlier_Tinba_indices)
    #print('anomalies Tinba',n_outliers_Tinba)
    
    n_outliers_TrickBot = len(outlier_TrickBot_indices)
    #print('anomalies TrickBot',n_outliers_TrickBot)
    
    n_outliers_Trickster = len(outlier_Trickster_indices)
    #print('anomalies Trickster',n_outliers_Trickster)
    
    n_outliers_TrojanDownloader = len(outlier_TrojanDownloader_indices)
    #print('anomalies TrojanDownloader',n_outliers_TrojanDownloader)
    
    n_outliers_Ursnif = len(outlier_Ursnif_indices)
    #print('anomalies Ursnif',n_outliers_Ursnif)
    
    n_outliers_WebCompanion = len(outlier_WebCompanion_indices)
    #print('anomalies WebCompanion',n_outliers_WebCompanion)
    
    options = opt
    
    for i in range(batch_size):
        #print('i',i)
        if (i % 2 == 0):
            #print('normal-normal')
            sid = rng.choice(n_inliers, 1)
            sid2 = rng.choice(n_inliers, 1)
            ref[i] = x_train[inlier_indices[sid]]
            ref2[i] = x_train[inlier_indices[sid2]]
            training_labels += [0]
            training_labels2 += [0]
            training_labels3 += [1]
        
        #1
        elif (i % 20 == 1):
            option=options[0]
            ref[i], ref2[i], training_labels, training_labels2, training_labels3 = poolref(training_labels, training_labels2, training_labels3,option,x_train, n_inliers, n_outliers, outlier_indices, inlier_indices, n_outliers_Adload, n_outliers_Artemis, n_outliers_BitCoinMiner,n_outliers_CCleaner,n_outliers_Cobalt,n_outliers_Downware,n_outliers_Dridex,n_outliers_Emotet,n_outliers_HTBot,n_outliers_MagicHound,n_outliers_MinerTrojan, n_outliers_PUA,n_outliers_Ramnit,n_outliers_Sality,n_outliers_Tinba,n_outliers_TrickBot,n_outliers_Trickster,n_outliers_TrojanDownloader,n_outliers_Ursnif,n_outliers_WebCompanion,outlier_Adload_indices, outlier_Artemis_indices, outlier_BitCoinMiner_indices,outlier_CCleaner_indices, outlier_Cobalt_indices, outlier_Downware_indices,outlier_Dridex_indices, outlier_Emotet_indices, outlier_HTBot_indices,outlier_MagicHound_indices, outlier_MinerTrojan_indices, outlier_PUA_indices,outlier_Ramnit_indices, outlier_Sality_indices, outlier_Tinba_indices,outlier_TrickBot_indices, outlier_Trickster_indices, outlier_TrojanDownloader_indices,outlier_Ursnif_indices,outlier_WebCompanion_indices,batch_size,rng) 
        
        elif (i % 20 == 3):
            option=options[1]
            ref[i], ref2[i], training_labels, training_labels2, training_labels3 = poolref(training_labels, training_labels2, training_labels3,option,x_train, n_inliers, n_outliers, outlier_indices, inlier_indices, n_outliers_Adload, n_outliers_Artemis, n_outliers_BitCoinMiner,n_outliers_CCleaner,n_outliers_Cobalt,n_outliers_Downware,n_outliers_Dridex,n_outliers_Emotet,n_outliers_HTBot,n_outliers_MagicHound,n_outliers_MinerTrojan, n_outliers_PUA,n_outliers_Ramnit,n_outliers_Sality,n_outliers_Tinba,n_outliers_TrickBot,n_outliers_Trickster,n_outliers_TrojanDownloader,n_outliers_Ursnif,n_outliers_WebCompanion,outlier_Adload_indices, outlier_Artemis_indices, outlier_BitCoinMiner_indices,outlier_CCleaner_indices, outlier_Cobalt_indices, outlier_Downware_indices,outlier_Dridex_indices, outlier_Emotet_indices, outlier_HTBot_indices,outlier_MagicHound_indices, outlier_MinerTrojan_indices, outlier_PUA_indices,outlier_Ramnit_indices, outlier_Sality_indices, outlier_Tinba_indices,outlier_TrickBot_indices, outlier_Trickster_indices, outlier_TrojanDownloader_indices,outlier_Ursnif_indices,outlier_WebCompanion_indices,batch_size,rng)
        
        elif (i % 20 == 5):
            option=options[2]
            ref[i], ref2[i], training_labels, training_labels2, training_labels3 = poolref(training_labels, training_labels2, training_labels3,option,x_train, n_inliers, n_outliers, outlier_indices, inlier_indices, n_outliers_Adload, n_outliers_Artemis, n_outliers_BitCoinMiner,n_outliers_CCleaner,n_outliers_Cobalt,n_outliers_Downware,n_outliers_Dridex,n_outliers_Emotet,n_outliers_HTBot,n_outliers_MagicHound,n_outliers_MinerTrojan, n_outliers_PUA,n_outliers_Ramnit,n_outliers_Sality,n_outliers_Tinba,n_outliers_TrickBot,n_outliers_Trickster,n_outliers_TrojanDownloader,n_outliers_Ursnif,n_outliers_WebCompanion,outlier_Adload_indices, outlier_Artemis_indices, outlier_BitCoinMiner_indices,outlier_CCleaner_indices, outlier_Cobalt_indices, outlier_Downware_indices,outlier_Dridex_indices, outlier_Emotet_indices, outlier_HTBot_indices,outlier_MagicHound_indices, outlier_MinerTrojan_indices, outlier_PUA_indices,outlier_Ramnit_indices, outlier_Sality_indices, outlier_Tinba_indices,outlier_TrickBot_indices, outlier_Trickster_indices, outlier_TrojanDownloader_indices,outlier_Ursnif_indices,outlier_WebCompanion_indices,batch_size,rng)
            
        elif (i % 20 == 7):
            option=options[3]
            ref[i], ref2[i], training_labels, training_labels2, training_labels3 = poolref(training_labels, training_labels2, training_labels3,option,x_train, n_inliers, n_outliers, outlier_indices, inlier_indices, n_outliers_Adload, n_outliers_Artemis, n_outliers_BitCoinMiner,n_outliers_CCleaner,n_outliers_Cobalt,n_outliers_Downware,n_outliers_Dridex,n_outliers_Emotet,n_outliers_HTBot,n_outliers_MagicHound,n_outliers_MinerTrojan, n_outliers_PUA,n_outliers_Ramnit,n_outliers_Sality,n_outliers_Tinba,n_outliers_TrickBot,n_outliers_Trickster,n_outliers_TrojanDownloader,n_outliers_Ursnif,n_outliers_WebCompanion,outlier_Adload_indices, outlier_Artemis_indices, outlier_BitCoinMiner_indices,outlier_CCleaner_indices, outlier_Cobalt_indices, outlier_Downware_indices,outlier_Dridex_indices, outlier_Emotet_indices, outlier_HTBot_indices,outlier_MagicHound_indices, outlier_MinerTrojan_indices, outlier_PUA_indices,outlier_Ramnit_indices, outlier_Sality_indices, outlier_Tinba_indices,outlier_TrickBot_indices, outlier_Trickster_indices, outlier_TrojanDownloader_indices,outlier_Ursnif_indices,outlier_WebCompanion_indices,batch_size,rng)
        
        elif (i % 20 == 9):
            option=options[4]
            ref[i], ref2[i], training_labels, training_labels2, training_labels3 = poolref(training_labels, training_labels2, training_labels3,option,x_train, n_inliers, n_outliers, outlier_indices, inlier_indices, n_outliers_Adload, n_outliers_Artemis, n_outliers_BitCoinMiner,n_outliers_CCleaner,n_outliers_Cobalt,n_outliers_Downware,n_outliers_Dridex,n_outliers_Emotet,n_outliers_HTBot,n_outliers_MagicHound,n_outliers_MinerTrojan, n_outliers_PUA,n_outliers_Ramnit,n_outliers_Sality,n_outliers_Tinba,n_outliers_TrickBot,n_outliers_Trickster,n_outliers_TrojanDownloader,n_outliers_Ursnif,n_outliers_WebCompanion,outlier_Adload_indices, outlier_Artemis_indices, outlier_BitCoinMiner_indices,outlier_CCleaner_indices, outlier_Cobalt_indices, outlier_Downware_indices,outlier_Dridex_indices, outlier_Emotet_indices, outlier_HTBot_indices,outlier_MagicHound_indices, outlier_MinerTrojan_indices, outlier_PUA_indices,outlier_Ramnit_indices, outlier_Sality_indices, outlier_Tinba_indices,outlier_TrickBot_indices, outlier_Trickster_indices, outlier_TrojanDownloader_indices,outlier_Ursnif_indices,outlier_WebCompanion_indices,batch_size,rng)
        
        elif (i % 20 == 11):
            option=options[5]
            ref[i], ref2[i], training_labels, training_labels2, training_labels3 = poolref(training_labels, training_labels2, training_labels3,option,x_train, n_inliers, n_outliers, outlier_indices, inlier_indices, n_outliers_Adload, n_outliers_Artemis, n_outliers_BitCoinMiner,n_outliers_CCleaner,n_outliers_Cobalt,n_outliers_Downware,n_outliers_Dridex,n_outliers_Emotet,n_outliers_HTBot,n_outliers_MagicHound,n_outliers_MinerTrojan, n_outliers_PUA,n_outliers_Ramnit,n_outliers_Sality,n_outliers_Tinba,n_outliers_TrickBot,n_outliers_Trickster,n_outliers_TrojanDownloader,n_outliers_Ursnif,n_outliers_WebCompanion,outlier_Adload_indices, outlier_Artemis_indices, outlier_BitCoinMiner_indices,outlier_CCleaner_indices, outlier_Cobalt_indices, outlier_Downware_indices,outlier_Dridex_indices, outlier_Emotet_indices, outlier_HTBot_indices,outlier_MagicHound_indices, outlier_MinerTrojan_indices, outlier_PUA_indices,outlier_Ramnit_indices, outlier_Sality_indices, outlier_Tinba_indices,outlier_TrickBot_indices, outlier_Trickster_indices, outlier_TrojanDownloader_indices,outlier_Ursnif_indices,outlier_WebCompanion_indices,batch_size,rng)
        
        elif (i % 20 == 13):
            option=options[6]
            ref[i], ref2[i], training_labels, training_labels2, training_labels3 = poolref(training_labels, training_labels2, training_labels3,option,x_train, n_inliers, n_outliers, outlier_indices, inlier_indices, n_outliers_Adload, n_outliers_Artemis, n_outliers_BitCoinMiner,n_outliers_CCleaner,n_outliers_Cobalt,n_outliers_Downware,n_outliers_Dridex,n_outliers_Emotet,n_outliers_HTBot,n_outliers_MagicHound,n_outliers_MinerTrojan, n_outliers_PUA,n_outliers_Ramnit,n_outliers_Sality,n_outliers_Tinba,n_outliers_TrickBot,n_outliers_Trickster,n_outliers_TrojanDownloader,n_outliers_Ursnif,n_outliers_WebCompanion,outlier_Adload_indices, outlier_Artemis_indices, outlier_BitCoinMiner_indices,outlier_CCleaner_indices, outlier_Cobalt_indices, outlier_Downware_indices,outlier_Dridex_indices, outlier_Emotet_indices, outlier_HTBot_indices,outlier_MagicHound_indices, outlier_MinerTrojan_indices, outlier_PUA_indices,outlier_Ramnit_indices, outlier_Sality_indices, outlier_Tinba_indices,outlier_TrickBot_indices, outlier_Trickster_indices, outlier_TrojanDownloader_indices,outlier_Ursnif_indices,outlier_WebCompanion_indices,batch_size,rng)
        
        elif (i % 20 == 15):
            option=options[7]
            ref[i], ref2[i], training_labels, training_labels2, training_labels3 = poolref(training_labels, training_labels2, training_labels3,option,x_train, n_inliers, n_outliers, outlier_indices, inlier_indices, n_outliers_Adload, n_outliers_Artemis, n_outliers_BitCoinMiner,n_outliers_CCleaner,n_outliers_Cobalt,n_outliers_Downware,n_outliers_Dridex,n_outliers_Emotet,n_outliers_HTBot,n_outliers_MagicHound,n_outliers_MinerTrojan, n_outliers_PUA,n_outliers_Ramnit,n_outliers_Sality,n_outliers_Tinba,n_outliers_TrickBot,n_outliers_Trickster,n_outliers_TrojanDownloader,n_outliers_Ursnif,n_outliers_WebCompanion,outlier_Adload_indices, outlier_Artemis_indices, outlier_BitCoinMiner_indices,outlier_CCleaner_indices, outlier_Cobalt_indices, outlier_Downware_indices,outlier_Dridex_indices, outlier_Emotet_indices, outlier_HTBot_indices,outlier_MagicHound_indices, outlier_MinerTrojan_indices, outlier_PUA_indices,outlier_Ramnit_indices, outlier_Sality_indices, outlier_Tinba_indices,outlier_TrickBot_indices, outlier_Trickster_indices, outlier_TrojanDownloader_indices,outlier_Ursnif_indices,outlier_WebCompanion_indices,batch_size,rng)
        
        elif (i % 20 == 17):
            option=options[8]
            ref[i], ref2[i], training_labels, training_labels2, training_labels3 = poolref(training_labels, training_labels2, training_labels3,option,x_train, n_inliers, n_outliers, outlier_indices, inlier_indices, n_outliers_Adload, n_outliers_Artemis, n_outliers_BitCoinMiner,n_outliers_CCleaner,n_outliers_Cobalt,n_outliers_Downware,n_outliers_Dridex,n_outliers_Emotet,n_outliers_HTBot,n_outliers_MagicHound,n_outliers_MinerTrojan, n_outliers_PUA,n_outliers_Ramnit,n_outliers_Sality,n_outliers_Tinba,n_outliers_TrickBot,n_outliers_Trickster,n_outliers_TrojanDownloader,n_outliers_Ursnif,n_outliers_WebCompanion,outlier_Adload_indices, outlier_Artemis_indices, outlier_BitCoinMiner_indices,outlier_CCleaner_indices, outlier_Cobalt_indices, outlier_Downware_indices,outlier_Dridex_indices, outlier_Emotet_indices, outlier_HTBot_indices,outlier_MagicHound_indices, outlier_MinerTrojan_indices, outlier_PUA_indices,outlier_Ramnit_indices, outlier_Sality_indices, outlier_Tinba_indices,outlier_TrickBot_indices, outlier_Trickster_indices, outlier_TrojanDownloader_indices,outlier_Ursnif_indices,outlier_WebCompanion_indices,batch_size,rng)
        
        elif (i % 20 == 19):
            option=options[9]
            ref[i], ref2[i], training_labels, training_labels2, training_labels3 = poolref(training_labels, training_labels2, training_labels3,option,x_train, n_inliers, n_outliers, outlier_indices, inlier_indices, n_outliers_Adload, n_outliers_Artemis, n_outliers_BitCoinMiner,n_outliers_CCleaner,n_outliers_Cobalt,n_outliers_Downware,n_outliers_Dridex,n_outliers_Emotet,n_outliers_HTBot,n_outliers_MagicHound,n_outliers_MinerTrojan, n_outliers_PUA,n_outliers_Ramnit,n_outliers_Sality,n_outliers_Tinba,n_outliers_TrickBot,n_outliers_Trickster,n_outliers_TrojanDownloader,n_outliers_Ursnif,n_outliers_WebCompanion,outlier_Adload_indices, outlier_Artemis_indices, outlier_BitCoinMiner_indices,outlier_CCleaner_indices, outlier_Cobalt_indices, outlier_Downware_indices,outlier_Dridex_indices, outlier_Emotet_indices, outlier_HTBot_indices,outlier_MagicHound_indices, outlier_MinerTrojan_indices, outlier_PUA_indices,outlier_Ramnit_indices, outlier_Sality_indices, outlier_Tinba_indices,outlier_TrickBot_indices, outlier_Trickster_indices, outlier_TrojanDownloader_indices,outlier_Ursnif_indices,outlier_WebCompanion_indices,batch_size,rng)
        
        
    return np.array(ref), np.array(training_labels)
    #return [np.array(ref),np.array(ref2)], [np.array(training_labels3),np.array(training_labels)]
 

def input_batch_generation_sup_sparse(x_train, outlier_indices, inlier_indices, batch_size, rng):
    '''
    batchs of samples. This is for libsvm stored sparse data.
    Alternates between positive and negative pairs.
    '''
    ref = np.empty((batch_size))
    training_labels = []
    n_inliers = len(inlier_indices)
    n_outliers = len(outlier_indices)
    for i in range(batch_size):
        if (i % 2 == 0):
            sid = rng.choice(n_inliers, 1)
            ref[i] = inlier_indices[sid]
            training_labels += [0]
        else:
            sid = rng.choice(n_outliers, 1)
            ref[i] = outlier_indices[sid]
            training_labels += [1]
    ref = x_train[ref, :].toarray()
    return ref, np.array(training_labels)


def load_model_weight_predict(model_name, input_shape, network_depth, x_test):
    '''
    load the saved weights to make predictions
    '''
    model = deviation_network(input_shape, network_depth)
    model.load_weights(model_name)
    scoring_network = Model(inputs=model.input, outputs=model.output)

    if data_format == 0:
        scores = scoring_network.predict(x_test)
    else:
        data_size = x_test.shape[0]
        scores = np.zeros([data_size, 1])
        count = 512
        i = 0
        while i < data_size:
            subset = x_test[i:count].toarray()
            scores[i:count] = scoring_network.predict(subset)
            if i % 1024 == 0:
                print(i)
            i = count
            count += 512
            if count > data_size:
                count = data_size
        assert count == data_size
    return scores


def inject_noise_sparse(seed, n_out, random_seed):
    '''
    add anomalies to training data to replicate anomaly contaminated data sets.
    we randomly swape 5% features of anomalies to avoid duplicate contaminated anomalies.
    This is for sparse data.
    '''
    rng = np.random.RandomState(random_seed)
    n_sample, dim = seed.shape
    swap_ratio = 0.05
    n_swap_feat = int(swap_ratio * dim)
    seed = seed.tocsc()
    noise = csc_matrix((n_out, dim))
    #print(noise.shape)
    for i in np.arange(n_out):
        outlier_idx = rng.choice(n_sample, 2, replace=False)
        o1 = seed[outlier_idx[0]]
        o2 = seed[outlier_idx[1]]
        swap_feats = rng.choice(dim, n_swap_feat, replace=False)
        noise[i] = o1.copy()
        noise[i, swap_feats] = o2[0, swap_feats]
    return noise.tocsr()


def inject_noise(seed, n_out, random_seed):
    '''
    add anomalies to training data to replicate anomaly contaminated data sets.
    we randomly swape 5% features of anomalies to avoid duplicate contaminated anomalies.
    this is for dense data
    '''
    rng = np.random.RandomState(random_seed)
    n_sample, dim = seed.shape
    swap_ratio = 0.05
    n_swap_feat = int(swap_ratio * dim)
    noise = np.empty((n_out, dim))
    for i in np.arange(n_out):
        outlier_idx = rng.choice(n_sample, 2, replace=False)
        o1 = seed[outlier_idx[0]]
        o2 = seed[outlier_idx[1]]
        swap_feats = rng.choice(dim, n_swap_feat, replace=False)
        noise[i] = o1.copy()
        noise[i, swap_feats] = o2[swap_feats]
    return noise


def run_devnet(args):
    names = args.data_set.split(',')
    names = ['x_train_NetML']
    network_depth = int(args.network_depth)
    random_seed = args.ramdn_seed
    for nm in names:
        runs = args.runs
        rauc = np.zeros(runs)
        ap = np.zeros(runs)
        filename = nm.strip()
        global data_format
        data_format = int(args.data_format)
        if data_format == 0:
            x, labels = dataLoading()
        else:
            x, labels = get_data_from_svmlight_file(args.input_path + filename + ".svm")
            x = x.tocsr()
        print("type x",type(x))
        x_narr = x.drop(['Adload','Artemis','BitCoinMiner','CCleaner','Cobalt','Downware','Dridex','Emotet','HTBot','MagicHound','MinerTrojan','PUA','Ramnit','Sality','Tinba','TrickBot','Trickster','TrojanDownloader','Ursnif','WebCompanion','benign'], axis = 1)
        print("shape x_narr",x_narr.shape)
        x_narr = x_narr.values
        labels_narr = labels.values 
        outlier_indices = np.where(labels == 1)[0]
        outliers = x_narr[outlier_indices]
        n_outliers_org = outliers.shape[0]

        train_time = 0
        test_time = 0
        
        ty = range(1,11)
        
        for n in ty:
            
            
            if n==1:
                opt = [1,2,3,4,6,7,8,9,10,11] 
            
            elif n==2:
                opt = [11, 7, 8, 2, 10, 4, 9, 19, 18, 12] 
                
            elif n==3:
                opt = [10, 3, 17, 20, 1, 8, 7, 2, 4, 12]
                
            elif n==4:
                opt = [16, 1, 9, 6, 11, 17, 15, 12, 7, 10]
            
            elif n==5:
                opt = [3, 6, 10, 16, 15, 20, 1, 2, 4, 17]
                
            elif n==6:
                opt = [15, 9, 17, 11, 20, 10, 2, 1, 18, 16]
            
            elif n==7:
                opt = [4, 2, 10, 11, 3, 7, 16, 18, 20, 17]
            
            elif n==8:
                opt = [1, 8, 6, 18, 11, 19, 16, 4, 10, 2]
                
            elif n==9:
                opt = [20, 9, 7, 8, 1, 19, 15, 4, 3, 11]
                
            elif n==10:
                opt = [10, 7, 2, 11, 8, 20, 19, 17, 12, 1]
            
            for i in np.arange(runs):
                x_train, x_test, y_train, y_test = train_test_split(x, labels, test_size=0.2, random_state=42, stratify=labels)
                
                attacks_train = x_train[['Adload','Artemis','BitCoinMiner','CCleaner','Cobalt','Downware','Dridex','Emotet','HTBot','MagicHound','MinerTrojan','PUA','Ramnit','Sality','Tinba','TrickBot','Trickster','TrojanDownloader','Ursnif','WebCompanion','benign']]
                
                y_train = np.array(y_train)
                y_test = np.array(y_test)
                
                
                attack_Adload_train_pd = x_train['Adload']
                attack_Artemis_train_pd = x_train['Artemis']
                attack_BitCoinMiner_train_pd = x_train['BitCoinMiner']
                attack_CCleaner_train_pd = x_train['CCleaner']
                attack_Cobalt_train_pd = x_train['Cobalt']
                attack_Downware_train_pd = x_train['Downware']
                attack_Dridex_train_pd = x_train['Dridex']
                attack_Emotet_train_pd = x_train['Emotet']
                attack_HTBot_train_pd = x_train['HTBot']
                attack_MagicHound_train_pd = x_train['MagicHound']
                attack_MinerTrojan_train_pd = x_train['MinerTrojan']
                attack_PUA_train_pd = x_train['PUA']
                attack_Ramnit_train_pd = x_train['Ramnit']
                attack_Sality_train_pd = x_train['Sality']
                attack_Tinba_train_pd = x_train['Tinba']
                attack_TrickBot_train_pd = x_train['TrickBot']
                attack_Trickster_train_pd = x_train['Trickster']
                attack_TrojanDownloader_train_pd = x_train['TrojanDownloader']
                attack_Ursnif_train_pd = x_train['Ursnif']
                attack_WebCompanion_train_pd = x_train['WebCompanion']
                attack_normal_train_pd = x_train['benign']
                
                attack_Adload_test_pd = x_test['Adload']
                attack_Artemis_test_pd = x_test['Artemis']
                attack_BitCoinMiner_test_pd = x_test['BitCoinMiner']
                attack_CCleaner_test_pd = x_test['CCleaner']
                attack_Cobalt_test_pd = x_test['Cobalt']
                attack_Downware_test_pd = x_test['Downware']
                attack_Dridex_test_pd = x_test['Dridex']
                attack_Emotet_test_pd = x_test['Emotet']
                attack_HTBot_test_pd = x_train['HTBot']
                attack_MagicHound_test_pd = x_test['MagicHound']
                attack_MinerTrojan_test_pd = x_test['MinerTrojan']
                attack_PUA_test_pd = x_test['PUA']
                attack_Ramnit_test_pd = x_test['Ramnit']
                attack_Sality_test_pd = x_test['Sality']
                attack_Tinba_test_pd = x_test['Tinba']
                attack_TrickBot_test_pd = x_test['TrickBot']
                attack_Trickster_test_pd = x_train['Trickster']
                attack_TrojanDownloader_test_pd = x_test['TrojanDownloader']
                attack_Ursnif_test_pd = x_test['Ursnif']
                attack_WebCompanion_test_pd = x_test['WebCompanion']
                attack_normal_test_pd = x_test['benign']
                
                attack_Adload_train = np.array(attack_Adload_train_pd)
                attack_Artemis_train = np.array(attack_Artemis_train_pd)
                attack_BitCoinMiner_train = np.array(attack_BitCoinMiner_train_pd)
                attack_CCleaner_train = np.array(attack_CCleaner_train_pd)
                attack_Cobalt_train = np.array(attack_Cobalt_train_pd)
                attack_Downware_train = np.array(attack_Downware_train_pd)
                attack_Dridex_train = np.array(attack_Dridex_train_pd)
                attack_Emotet_train = np.array(attack_Emotet_train_pd)
                attack_HTBot_train = np.array(attack_HTBot_train_pd)
                attack_MagicHound_train = np.array(attack_MagicHound_train_pd)
                attack_MinerTrojan_train = np.array(attack_MinerTrojan_train_pd)
                attack_PUA_train = np.array(attack_PUA_train_pd)
                attack_Ramnit_train = np.array(attack_Ramnit_train_pd)
                attack_Sality_train = np.array(attack_Sality_train_pd)
                attack_Tinba_train = np.array(attack_Tinba_train_pd)
                attack_TrickBot_train = np.array(attack_TrickBot_train_pd)
                attack_Trickster_train = np.array(attack_Trickster_train_pd)
                attack_TrojanDownloader_train = np.array(attack_TrojanDownloader_train_pd)
                attack_Ursnif_train = np.array(attack_Ursnif_train_pd)
                attack_WebCompanion_train = np.array(attack_WebCompanion_train_pd)
                attack_normal_train = np.array(attack_normal_train_pd)
                
                attack_Adload_test = np.array(attack_Adload_test_pd)
                attack_Artemis_test = np.array(attack_Artemis_test_pd)
                attack_BitCoinMiner_test = np.array(attack_BitCoinMiner_test_pd)
                attack_CCleaner_test = np.array(attack_CCleaner_test_pd)
                attack_Cobalt_test = np.array(attack_Cobalt_test_pd)
                attack_Downware_test = np.array(attack_Downware_test_pd)
                attack_Dridex_test = np.array(attack_Dridex_test_pd)
                attack_Emotet_test = np.array(attack_Emotet_test_pd)
                attack_HTBot_test = np.array(attack_HTBot_test_pd)
                attack_MagicHound_test = np.array(attack_MagicHound_test_pd)
                attack_MinerTrojan_test = np.array(attack_MinerTrojan_test_pd)
                attack_PUA_test = np.array(attack_PUA_test_pd)
                attack_Ramnit_test = np.array(attack_Ramnit_test_pd)
                attack_Sality_test = np.array(attack_Sality_test_pd)
                attack_Tinba_test = np.array(attack_Tinba_test_pd)
                attack_TrickBot_test = np.array(attack_TrickBot_test_pd)
                attack_Trickster_test = np.array(attack_Trickster_test_pd)
                attack_TrojanDownloader_test = np.array(attack_TrojanDownloader_test_pd)
                attack_Ursnif_test = np.array(attack_Ursnif_test_pd)
                attack_WebCompanion_test = np.array(attack_WebCompanion_test_pd)
                attack_normal_test = np.array(attack_normal_test_pd)
            
                print(filename + ': round ' + str(i))
                outlier_indices = np.where(y_train == 1)[0]
                inlier_indices = np.where(y_train == 0)[0]
                
                
                
                outlier_Adload_indices = np.where(attack_Adload_train == 1)[0]
                outlier_Artemis_indices = np.where(attack_Artemis_train == 1)[0]
                outlier_BitCoinMiner_indices = np.where(attack_BitCoinMiner_train == 1)[0]
                outlier_CCleaner_indices = np.where(attack_CCleaner_train == 1)[0]
                outlier_Cobalt_indices = np.where(attack_Cobalt_train == 1)[0]
                outlier_Downware_indices = np.where(attack_Downware_train == 1)[0]
                outlier_Dridex_indices = np.where(attack_Dridex_train == 1)[0]
                outlier_Emotet_indices = np.where(attack_Emotet_train == 1)[0] 
                outlier_HTBot_indices = np.where(attack_HTBot_train == 1)[0] 
                outlier_MagicHound_indices = np.where(attack_MagicHound_train == 1)[0]
                outlier_MinerTrojan_indices = np.where(attack_MinerTrojan_train == 1)[0]
                outlier_PUA_indices = np.where(attack_PUA_train == 1)[0]
                outlier_Ramnit_indices = np.where(attack_Ramnit_train == 1)[0]
                outlier_Sality_indices = np.where(attack_Sality_train == 1)[0]
                outlier_Tinba_indices = np.where(attack_Tinba_train == 1)[0]
                outlier_TrickBot_indices = np.where(attack_TrickBot_train == 1)[0]
                outlier_Trickster_indices = np.where(attack_Trickster_train == 1)[0] 
                outlier_TrojanDownloader_indices = np.where(attack_TrojanDownloader_train == 1)[0] 
                outlier_Ursnif_indices = np.where(attack_Ursnif_train == 1)[0]
                outlier_WebCompanion_indices = np.where(attack_WebCompanion_train == 1)[0] 
        
                normal_indices = np.where(attack_normal_train == 1)[0] 
                
                outlier_Adload_indices_test = np.where(attack_Adload_test == 1)[0]
                outlier_Artemis_indices_test = np.where(attack_Artemis_test == 1)[0]
                outlier_BitCoinMiner_indices_test = np.where(attack_BitCoinMiner_test == 1)[0]
                outlier_CCleaner_indices_test = np.where(attack_CCleaner_test == 1)[0]
                outlier_Cobalt_indices_test = np.where(attack_Cobalt_test == 1)[0]
                outlier_Downware_indices_test = np.where(attack_Downware_test == 1)[0]
                outlier_Dridex_indices_test = np.where(attack_Dridex_test == 1)[0]
                outlier_Emotet_indices_test = np.where(attack_Emotet_test == 1)[0] 
                outlier_HTBot_indices_test = np.where(attack_HTBot_test == 1)[0] 
                outlier_MagicHound_indices_test = np.where(attack_MagicHound_test == 1)[0]
                outlier_MinerTrojan_indices_test = np.where(attack_MinerTrojan_test == 1)[0]
                outlier_PUA_indices_test = np.where(attack_PUA_test == 1)[0]
                outlier_Ramnit_indices_test = np.where(attack_Ramnit_test == 1)[0]
                outlier_Sality_indices_test = np.where(attack_Sality_test == 1)[0]
                outlier_Tinba_indices_test = np.where(attack_Tinba_test == 1)[0]
                outlier_TrickBot_indices_test = np.where(attack_TrickBot_test == 1)[0]
                outlier_Trickster_indices_test = np.where(attack_Trickster_test == 1)[0] 
                outlier_TrojanDownloader_indices_test = np.where(attack_TrojanDownloader_test == 1)[0] 
                outlier_Ursnif_indices_test = np.where(attack_Ursnif_test== 1)[0]
                outlier_WebCompanion_indices_test = np.where(attack_WebCompanion_test == 1)[0] 
                
                normal_indices_test = np.where(attack_normal_test == 1)[0]
                
                print("========Train original anomalies============")
                
                n_outlier_Adload = len(outlier_Adload_indices) 
                print("Adload attack number ", n_outlier_Adload)
                
                n_outlier_Artemis = len(outlier_Artemis_indices) 
                print("Artemis attack number ", n_outlier_Artemis)
                
                n_outlier_BitCoinMiner = len(outlier_BitCoinMiner_indices) 
                print("BitCoinMiner attack number ", n_outlier_BitCoinMiner)
                
                n_outlier_CCleaner = len(outlier_CCleaner_indices) 
                print("CCleaner attacks number ", n_outlier_CCleaner)
                
                n_outlier_Cobalt = len(outlier_Cobalt_indices) 
                print("Cobalt attack number ", n_outlier_Cobalt)
                
                n_outlier_Downware = len(outlier_Downware_indices) 
                print("Downware attack number ", n_outlier_Downware)
                
                n_outlier_Dridex = len(outlier_Dridex_indices) 
                print("Dridex attack number ", n_outlier_Dridex)
                
                n_outlier_Emotet = len(outlier_Emotet_indices) 
                print("Emotet attack number ", n_outlier_Emotet)
                
                n_outlier_HTBot = len(outlier_HTBot_indices) 
                print("HTBot attack number ", n_outlier_HTBot)
                
                n_outlier_MagicHound = len(outlier_MagicHound_indices) 
                print("MagicHound attack number ", n_outlier_MagicHound)
                
                n_outlier_MinerTrojan = len(outlier_MinerTrojan_indices) 
                print("MinerTrojan attack number ", n_outlier_MinerTrojan)
                
                n_outlier_PUA = len(outlier_PUA_indices) 
                print("PUA attack number ", n_outlier_PUA)
                
                n_outlier_Ramnit = len(outlier_Ramnit_indices) 
                print("Ramnit attack number ", n_outlier_Ramnit)
                
                n_outlier_Sality = len(outlier_Sality_indices) 
                print("Sality attack number ", n_outlier_Sality)
                
                n_outlier_Tinba = len(outlier_Tinba_indices) 
                print("Tinba attack number ", n_outlier_Tinba)
                
                n_outlier_TrickBot = len(outlier_TrickBot_indices) 
                print("TrickBot attack number ", n_outlier_TrickBot)
                
                n_outlier_Trickster = len(outlier_Trickster_indices) 
                print("Trickster attack number ", n_outlier_Trickster)
                
                n_outlier_TrojanDownloader = len(outlier_TrojanDownloader_indices) 
                print("TrojanDownloader attack number ", n_outlier_TrojanDownloader)
                
                n_outlier_Ursnif = len(outlier_Ursnif_indices) 
                print("Ursnif attack number ", n_outlier_Ursnif)
                
                n_outlier_WebCompanion = len(outlier_WebCompanion_indices) 
                print("WebCompanion attack number ", n_outlier_WebCompanion)
                
                n_normal = len(normal_indices) 
                print("normal number ", n_normal)
                
                print("========Test original anomalies============")
                
                n_outlier_Adload_test = len(outlier_Adload_indices_test) 
                print("Adload attack number ", n_outlier_Adload_test)
                
                n_outlier_Artemis_test = len(outlier_Artemis_indices_test) 
                print("Artemis attack number ", n_outlier_Artemis_test)
                
                n_outlier_BitCoinMiner_test = len(outlier_BitCoinMiner_indices_test) 
                print("BitCoinMiner attack number ", n_outlier_BitCoinMiner_test)
                
                n_outlier_CCleaner_test = len(outlier_CCleaner_indices_test) 
                print("CCleaner attacks number ", n_outlier_CCleaner_test)
                
                n_outlier_Cobalt_test = len(outlier_Cobalt_indices_test) 
                print("Cobalt attack number ", n_outlier_Cobalt_test)
                
                n_outlier_Downware_test = len(outlier_Downware_indices_test) 
                print("Downware attack number ", n_outlier_Downware_test)
                
                n_outlier_Dridex_test = len(outlier_Dridex_indices_test) 
                print("Dridex attack number ", n_outlier_Dridex_test)
                
                n_outlier_Emotet_test = len(outlier_Emotet_indices_test) 
                print("Emotet attack number ", n_outlier_Emotet_test)
                
                n_outlier_HTBot_test = len(outlier_HTBot_indices_test) 
                print("HTBot attack number ", n_outlier_HTBot_test)
                
                n_outlier_MagicHound_test = len(outlier_MagicHound_indices_test) 
                print("MagicHound attack number ", n_outlier_MagicHound_test)
                
                n_outlier_MinerTrojan_test = len(outlier_MinerTrojan_indices_test) 
                print("MinerTrojan attack number ", n_outlier_MinerTrojan_test)
                
                n_outlier_PUA_test = len(outlier_PUA_indices_test) 
                print("PUA attack number ", n_outlier_PUA_test)
                
                n_outlier_Ramnit_test = len(outlier_Ramnit_indices_test) 
                print("Ramnit attack number ", n_outlier_Ramnit_test)
                
                n_outlier_Sality_test = len(outlier_Sality_indices_test) 
                print("Sality attack number ", n_outlier_Sality_test)
                
                n_outlier_Tinba_test = len(outlier_Tinba_indices_test) 
                print("Tinba attack number ", n_outlier_Tinba_test)
                
                n_outlier_TrickBot_test = len(outlier_TrickBot_indices_test) 
                print("TrickBot attack number ", n_outlier_TrickBot_test)
                
                n_outlier_Trickster_test = len(outlier_Trickster_indices_test) 
                print("rTrickster attack number ", n_outlier_Trickster_test)
                
                n_outlier_TrojanDownloader_test = len(outlier_TrojanDownloader_indices_test) 
                print("TrojanDownloader attack number ", n_outlier_TrojanDownloader_test)
                
                n_outlier_Ursnif_test = len(outlier_Ursnif_indices_test) 
                print("Ursnif attack number ", n_outlier_Ursnif_test)
                
                n_outlier_WebCompanion_test = len(outlier_WebCompanion_indices_test) 
                print("WebCompanion attack number ", n_outlier_WebCompanion_test)
                
                n_normal_test = len(normal_indices_test) 
                print("normal number test ", n_normal_test)
    
                n_outliers = len(outlier_indices)
                print("Original training size: %d, No. outliers: %d" % (x_train.shape[0], n_outliers))
                
                x_train = x_train.drop(['Adload','Artemis','BitCoinMiner','CCleaner','Cobalt','Downware','Dridex','Emotet','HTBot','MagicHound','MinerTrojan','PUA','Ramnit','Sality','Tinba','TrickBot','Trickster','TrojanDownloader','Ursnif','WebCompanion','benign'], axis = 1)
                x_test = x_test.drop(['Adload','Artemis','BitCoinMiner','CCleaner','Cobalt','Downware','Dridex','Emotet','HTBot','MagicHound','MinerTrojan','PUA','Ramnit','Sality','Tinba','TrickBot','Trickster','TrojanDownloader','Ursnif','WebCompanion','benign'], axis = 1)
                
                x_train = x_train.values
         
                x_test = x_test.values
                
                n_noise = len(np.where(y_train == 0)[0]) * args.cont_rate / (1. - args.cont_rate)
                n_noise = int(n_noise)
    
                rng = np.random.RandomState(random_seed)
                
                if data_format == 0:
                    if n_outliers > args.known_outliers:
                        
                        print("=======Train anomalies samples===========")
                        
                        if 1 in opt:
                            #1
                            mn_Adload = n_outlier_Adload - args.known_outliers
                            remove_idx_Adload = rng.choice(outlier_Adload_indices,  mn_Adload, replace=False)
                            final_outlier_Adload = n_outlier_Adload - len(remove_idx_Adload)
                            print("Adload anomalies", final_outlier_Adload)
                            
                        else:
                            #1
                            mn_Adload = n_outlier_Adload
                            remove_idx_Adload = rng.choice(outlier_Adload_indices,  mn_Adload, replace=False)
                            final_outlier_Adload = n_outlier_Adload - len(remove_idx_Adload)
                            print("Adload anomalies", final_outlier_Adload)
                            
                        
                        if 2 in opt:
                            #2
                            mn_Artemis = n_outlier_Artemis - args.known_outliers 
                            remove_idx_Artemis = rng.choice(outlier_Artemis_indices,  mn_Artemis, replace=False)
                            final_outlier_Artemis = n_outlier_Artemis - len(remove_idx_Artemis)
                            print("Artemis anomalies", final_outlier_Artemis)
                            
                        else:
                            #2
                            mn_Artemis = n_outlier_Artemis 
                            remove_idx_Artemis = rng.choice(outlier_Artemis_indices,  mn_Artemis, replace=False)
                            final_outlier_Artemis = n_outlier_Artemis - len(remove_idx_Artemis)
                            print("Artemis anomalies", final_outlier_Artemis)
                            
                        
                        if 3 in opt:
                            #3
                            mn_BitCoinMiner = n_outlier_BitCoinMiner - args.known_outliers
                            remove_idx_BitCoinMiner = rng.choice(outlier_BitCoinMiner_indices,  mn_BitCoinMiner, replace=False)
                            final_outlier_BitCoinMiner = n_outlier_BitCoinMiner - len(remove_idx_BitCoinMiner)
                            print("BitCoinMiner anomalies", final_outlier_BitCoinMiner)
                        
                        else:
                            #3
                            mn_BitCoinMiner = n_outlier_BitCoinMiner
                            remove_idx_BitCoinMiner = rng.choice(outlier_BitCoinMiner_indices,  mn_BitCoinMiner, replace=False)
                            final_outlier_BitCoinMiner = n_outlier_BitCoinMiner - len(remove_idx_BitCoinMiner)
                            print("BitCoinMiner anomalies", final_outlier_BitCoinMiner)
                        
                        if 4 in opt:
                            #4 
                            mn_CCleaner = n_outlier_CCleaner - args.known_outliers
                            remove_idx_CCleaner = rng.choice(outlier_CCleaner_indices,  mn_CCleaner, replace=False)
                            final_outlier_CCleaner = n_outlier_CCleaner - len(remove_idx_CCleaner)
                            print("CCleaner anomalies", final_outlier_CCleaner)
                        
                        else:
                            #4
                            mn_CCleaner = n_outlier_CCleaner 
                            remove_idx_CCleaner = rng.choice(outlier_CCleaner_indices,  mn_CCleaner, replace=False)    
                            final_outlier_CCleaner = n_outlier_CCleaner - len(remove_idx_CCleaner)
                            print("CCleaner anomalies", final_outlier_CCleaner)
                            
                        if 5 in opt:
                            #5 
                            mn_Cobalt = n_outlier_Cobalt - args.known_outliers
                            remove_idx_Cobalt= rng.choice(outlier_Cobalt_indices, mn_Cobalt, replace=False)
                            final_outlier_Cobalt = n_outlier_Cobalt - len(remove_idx_Cobalt)
                            print("Cobalt anomalies", final_outlier_Cobalt)
                        
                        else:
                            #5
                            mn_Cobalt = n_outlier_Cobalt 
                            remove_idx_Cobalt= rng.choice(outlier_Cobalt_indices, mn_Cobalt, replace=False)
                            final_outlier_Cobalt = n_outlier_Cobalt - len(remove_idx_Cobalt)
                            print("Cobalt anomalies", final_outlier_Cobalt)
                            
                        
                        if 6 in opt:
                            #6
                            mn_Downware = n_outlier_Downware - args.known_outliers
                            remove_idx_Downware = rng.choice(outlier_Downware_indices,  mn_Downware, replace=False)
                            final_outlier_Downware = n_outlier_Downware - len(remove_idx_Downware)
                            print("Downware anomalies", final_outlier_Downware)
                            
                        else:
                            #6
                            mn_Downware = n_outlier_Downware 
                            remove_idx_Downware = rng.choice(outlier_Downware_indices,  mn_Downware, replace=False)
                            final_outlier_Downware = n_outlier_Downware - len(remove_idx_Downware)
                            print("Downware anomalies", final_outlier_Downware)
                            
                        
                        if 7 in opt:
                            #7
                            mn_Dridex= n_outlier_Dridex - args.known_outliers
                            remove_idx_Dridex = rng.choice(outlier_Dridex_indices,  mn_Dridex, replace=False)
                            final_outlier_Dridex = n_outlier_Dridex - len(remove_idx_Dridex)
                            print("Dridex anomalies", final_outlier_Dridex)
                            
                        else:
                            #7
                            mn_Dridex = n_outlier_Dridex 
                            remove_idx_Dridex = rng.choice(outlier_Dridex_indices,  mn_Dridex, replace=False)
                            final_outlier_Dridex = n_outlier_Dridex - len(remove_idx_Dridex)
                            print("Dridex anomalies", final_outlier_Dridex)
                        
                        if 8 in opt:
                            #8
                            mn_Emotet = n_outlier_Emotet - args.known_outliers
                            remove_idx_Emotet = rng.choice(outlier_Emotet_indices,  mn_Emotet, replace=False)
                            final_outlier_Emotet = n_outlier_Emotet - len(remove_idx_Emotet)
                            print("Emotet anomalies", final_outlier_Emotet)
                            
                        else:
                            #8
                            mn_Emotet = n_outlier_Emotet 
                            remove_idx_Emotet = rng.choice(outlier_Emotet_indices,  mn_Emotet, replace=False)
                            final_outlier_Emotet = n_outlier_Emotet - len(remove_idx_Emotet)
                            print("Emotet anomalies", final_outlier_Emotet)
                          
                        if 9 in opt:
                            #9
                            mn_HTBot = n_outlier_HTBot - args.known_outliers
                            remove_idx_HTBot = rng.choice(outlier_HTBot_indices,  mn_HTBot, replace=False)
                            final_outlier_HTBot = n_outlier_HTBot - len(remove_idx_HTBot)
                            print("HTBot anomalies", final_outlier_HTBot)
                        
                        else:
                            #9
                            mn_HTBot = n_outlier_HTBot
                            remove_idx_HTBot = rng.choice(outlier_HTBot_indices,  mn_HTBot, replace=False)
                            final_outlier_HTBot = n_outlier_HTBot - len(remove_idx_HTBot)
                            print("HTBot anomalies", final_outlier_HTBot)
                        
                        if 10 in opt:
                            #10
                            mn_MagicHound = n_outlier_MagicHound - args.known_outliers
                            remove_idx_MagicHound = rng.choice(outlier_MagicHound_indices,  mn_MagicHound, replace=False)
                            final_outlier_MagicHound = n_outlier_MagicHound - len(remove_idx_MagicHound)
                            print("MagicHound anomalies", final_outlier_MagicHound)
                            
                        else:
                             #10
                            mn_MagicHound = n_outlier_MagicHound
                            remove_idx_MagicHound = rng.choice(outlier_MagicHound_indices,  mn_MagicHound, replace=False)
                            final_outlier_MagicHound = n_outlier_MagicHound - len(remove_idx_MagicHound)
                            print("MagicHound anomalies", final_outlier_MagicHound)
                        
                        if 11 in opt:
                            #11
                            mn_MinerTrojan = n_outlier_MinerTrojan - args.known_outliers
                            remove_idx_MinerTrojan = rng.choice(outlier_MinerTrojan_indices,  mn_MinerTrojan, replace=False)
                            final_outlier_MinerTrojan = n_outlier_MinerTrojan - len(remove_idx_MinerTrojan)
                            print("MinerTrojan anomalies", final_outlier_MinerTrojan)
                            
                        else:
                            #11
                            mn_MinerTrojan = n_outlier_MinerTrojan
                            remove_idx_MinerTrojan = rng.choice(outlier_MinerTrojan_indices,  mn_MinerTrojan, replace=False)
                            final_outlier_MinerTrojan = n_outlier_MinerTrojan - len(remove_idx_MinerTrojan)
                            print("MinerTrojan anomalies", final_outlier_MinerTrojan)
                        
                        if 12 in opt:
                            #12
                            mn_PUA = n_outlier_PUA  - args.known_outliers 
                            remove_idx_PUA = rng.choice(outlier_PUA_indices, mn_PUA, replace=False)
                            final_outlier_PUA  = n_outlier_PUA  - len(remove_idx_PUA)
                            print("PUA anomalies", final_outlier_PUA)
                            
                        else:
                            #12
                            mn_PUA  = n_outlier_PUA 
                            remove_idx_PUA = rng.choice(outlier_PUA_indices, mn_PUA, replace=False)
                            final_outlier_PUA  = n_outlier_PUA  - len(remove_idx_PUA)
                            print("PUA anomalies", final_outlier_PUA)
                        
                        if 13 in opt:
                            #13
                            mn_Ramnit = n_outlier_Ramnit - args.known_outliers
                            remove_idx_Ramnit = rng.choice(outlier_Ramnit_indices,  mn_Ramnit, replace=False)
                            final_outlier_Ramnit = n_outlier_Ramnit - len(remove_idx_Ramnit)
                            print("Ramnit anomalies", final_outlier_Ramnit)
                            
                        else:
                            #13
                            mn_Ramnit = n_outlier_Ramnit
                            remove_idx_Ramnit = rng.choice(outlier_Ramnit_indices,  mn_Ramnit, replace=False)
                            final_outlier_Ramnit = n_outlier_Ramnit - len(remove_idx_Ramnit)
                            print("Ramnit anomalies", final_outlier_Ramnit)
            
                        if 14 in opt:
                            #14
                            mn_Sality = n_outlier_Sality - args.known_outliers
                            remove_idx_Sality = rng.choice(outlier_Sality_indices,  mn_Sality, replace=False)
                            final_outlier_Sality = n_outlier_Sality - len(remove_idx_Sality)
                            print("Sality anomalies", final_outlier_Sality)
                            
                        else:
                            #14
                            mn_Sality = n_outlier_Sality
                            remove_idx_Sality = rng.choice(outlier_Sality_indices,  mn_Sality, replace=False)
                            final_outlier_Sality = n_outlier_Sality - len(remove_idx_Sality)
                            print("Sality anomalies", final_outlier_Sality)
                        
                        if 15 in opt:
                            #15
                            mn_Tinba = n_outlier_Tinba - args.known_outliers
                            remove_idx_Tinba = rng.choice(outlier_Tinba_indices,  mn_Tinba, replace=False)
                            final_outlier_Tinba = n_outlier_Tinba - len(remove_idx_Tinba)
                            print("Tinba anomalies", final_outlier_Tinba)
                            
                        else:
                            #15
                            mn_Tinba = n_outlier_Tinba
                            remove_idx_Tinba = rng.choice(outlier_Tinba_indices,  mn_Tinba, replace=False)
                            final_outlier_Tinba = n_outlier_Tinba - len(remove_idx_Tinba)
                            print("Tinba anomalies", final_outlier_Tinba)
                        
                        if 16 in opt:
                            #16
                            mn_TrickBot = n_outlier_TrickBot - args.known_outliers
                            remove_idx_TrickBot = rng.choice(outlier_TrickBot_indices,  mn_TrickBot, replace=False)
                            final_outlier_TrickBot = n_outlier_TrickBot - len(remove_idx_TrickBot)
                            print("TrickBotanomalies", final_outlier_TrickBot)
                            
                        else:
                            #16
                            mn_TrickBot = n_outlier_TrickBot
                            remove_idx_TrickBot = rng.choice(outlier_TrickBot_indices,  mn_TrickBot, replace=False)
                            final_outlier_TrickBot = n_outlier_TrickBot - len(remove_idx_TrickBot)
                            print("TrickBotanomalies", final_outlier_TrickBot)
                        
                        if 17 in opt:
                            #17
                            mn_Trickster = n_outlier_Trickster - args.known_outliers
                            remove_idx_Trickster = rng.choice(outlier_Trickster_indices,  mn_Trickster, replace=False)
                            final_outlier_Trickster = n_outlier_Trickster - len(remove_idx_Trickster)
                            print("Trickster anomalies", final_outlier_Trickster)
                        
                        else:
                             #17
                            mn_Trickster = n_outlier_Trickster
                            remove_idx_Trickster = rng.choice(outlier_Trickster_indices,  mn_Trickster, replace=False)
                            final_outlier_Trickster = n_outlier_Trickster - len(remove_idx_Trickster)
                            print("Trickster anomalies", final_outlier_Trickster)
                        
                        if 18 in opt:
                            #18
                            mn_TrojanDownloader = n_outlier_TrojanDownloader - args.known_outliers
                            remove_idx_TrojanDownloader = rng.choice(outlier_TrojanDownloader_indices,  mn_TrojanDownloader, replace=False)
                            final_outlier_TrojanDownloader = n_outlier_TrojanDownloader - len(remove_idx_TrojanDownloader)
                            print("TrojanDownloader anomalies", final_outlier_TrojanDownloader)
                            
                        else:
                             #18
                            mn_TrojanDownloader = n_outlier_TrojanDownloader
                            remove_idx_TrojanDownloader = rng.choice(outlier_TrojanDownloader_indices,  mn_TrojanDownloader, replace=False)
                            final_outlier_TrojanDownloader = n_outlier_TrojanDownloader - len(remove_idx_TrojanDownloader)
                            print("TrojanDownloader anomalies", final_outlier_TrojanDownloader)
                        
                        if 19 in opt:
                            #19
                            mn_Ursnif = n_outlier_Ursnif - args.known_outliers
                            remove_idx_Ursnif = rng.choice(outlier_Ursnif_indices,  mn_Ursnif, replace=False)
                            final_outlier_Ursnif = n_outlier_Ursnif - len(remove_idx_Ursnif)
                            print("Ursnif anomalies", final_outlier_Ursnif)
                            
                        else:
                            #19
                            mn_Ursnif = n_outlier_Ursnif
                            remove_idx_Ursnif = rng.choice(outlier_Ursnif_indices,  mn_Ursnif, replace=False)
                            final_outlier_Ursnif = n_outlier_Ursnif - len(remove_idx_Ursnif)
                            print("Ursnif anomalies", final_outlier_Ursnif)
                        
                        if 20 in opt:
                            #20
                            mn_WebCompanion = n_outlier_WebCompanion - args.known_outliers
                            remove_idx_WebCompanion = rng.choice(outlier_WebCompanion_indices,  mn_WebCompanion, replace=False)
                            final_outlier_WebCompanion = n_outlier_WebCompanion - len(remove_idx_WebCompanion)
                            print("WebCompanion anomalies", final_outlier_WebCompanion)
                        
                        else:
                            #20
                            mn_WebCompanion = n_outlier_WebCompanion
                            remove_idx_WebCompanion = rng.choice(outlier_WebCompanion_indices,  mn_WebCompanion, replace=False)
                            final_outlier_WebCompanion = n_outlier_WebCompanion - len(remove_idx_WebCompanion)
                            print("WebCompanion anomalies", final_outlier_WebCompanion)
                        
                        remove_idx = np.concatenate([remove_idx_Adload,remove_idx_Artemis,remove_idx_BitCoinMiner,remove_idx_CCleaner,remove_idx_Cobalt,remove_idx_Downware,remove_idx_Dridex,remove_idx_Emotet,remove_idx_HTBot,remove_idx_MagicHound,remove_idx_MinerTrojan,remove_idx_PUA,remove_idx_Ramnit,remove_idx_Sality,remove_idx_Tinba,remove_idx_TrickBot,remove_idx_Trickster,remove_idx_TrojanDownloader,remove_idx_Ursnif,remove_idx_WebCompanion])
                        
                        x_train = np.delete(x_train, remove_idx, axis=0)
                        y_train = np.delete(y_train, remove_idx, axis=0)
                        #print('ROB', x_train.shape)
                        
                        attack_Adload_train = np.delete(attack_Adload_train, remove_idx, axis=0)
                        attack_Artemis_train = np.delete(attack_Artemis_train, remove_idx, axis=0)
                        attack_BitCoinMiner_train = np.delete(attack_BitCoinMiner_train, remove_idx, axis=0)
                        attack_CCleaner_train = np.delete(attack_CCleaner_train, remove_idx, axis=0)
                        attack_Cobalt_train = np.delete(attack_Cobalt_train, remove_idx, axis=0)
                        attack_Downware_train = np.delete(attack_Downware_train, remove_idx, axis=0)
                        attack_Dridex_train = np.delete(attack_Dridex_train, remove_idx, axis=0)
                        attack_Emotet_train = np.delete(attack_Emotet_train, remove_idx, axis=0)
                        attack_HTBot_train = np.delete(attack_HTBot_train, remove_idx, axis=0 )
                        attack_MagicHound_train = np.delete(attack_MagicHound_train, remove_idx, axis=0)
                        attack_MinerTrojan_train = np.delete(attack_MinerTrojan_train, remove_idx, axis=0)
                        attack_PUA_train = np.delete(attack_PUA_train, remove_idx, axis=0)
                        attack_Ramnit_train = np.delete(attack_Ramnit_train, remove_idx, axis=0)
                        attack_Sality_train = np.delete(attack_Sality_train, remove_idx, axis=0)
                        attack_Tinba_train = np.delete(attack_Tinba_train, remove_idx, axis=0)
                        attack_TrickBot_train = np.delete(attack_TrickBot_train, remove_idx, axis=0)
                        attack_Trickster_train = np.delete(attack_Trickster_train, remove_idx, axis=0)
                        attack_TrojanDownloader_train = np.delete(attack_TrojanDownloader_train, remove_idx, axis=0)
                        attack_Ursnif_train = np.delete(attack_Ursnif_train, remove_idx, axis=0 )
                        attack_WebCompanion_train = np.delete(attack_WebCompanion_train, remove_idx, axis=0)
                        
                        attack_normal_train = np.delete(attack_normal_train, remove_idx, axis=0)
                        
                        print("===========Test anomalies samples====================")
                        
                        #1
                        mn_Adload_test = n_outlier_Adload_test - 739
                        remove_idx_Adload_test = rng.choice(outlier_Adload_indices_test,  mn_Adload_test, replace=False)
                        final_outlier_Adload_test = n_outlier_Adload_test - len(remove_idx_Adload_test)
                        print("Adload anomalies test", final_outlier_Adload_test)
                        
                        #2
                        mn_Artemis_test = n_outlier_Artemis_test - 739 
                        remove_idx_Artemis_test = rng.choice(outlier_Artemis_indices_test,  mn_Artemis_test, replace=False)
                        final_outlier_Artemis_test = n_outlier_Artemis_test - len(remove_idx_Artemis_test)
                        print("Artemis anomalies test", final_outlier_Artemis_test)
        
                        #3
                        mn_BitCoinMiner_test = n_outlier_BitCoinMiner_test - 739
                        remove_idx_BitCoinMiner_test = rng.choice(outlier_BitCoinMiner_indices_test, mn_BitCoinMiner_test, replace=False)
                        final_outlier_BitCoinMiner_test = n_outlier_BitCoinMiner_test - len(remove_idx_BitCoinMiner_test)
                        print("BitCoinMiner anomalies test", final_outlier_BitCoinMiner_test)
                        
                        #4 
                        mn_CCleaner_test = n_outlier_CCleaner_test - 739
                        remove_idx_CCleaner_test = rng.choice(outlier_CCleaner_indices_test,  mn_CCleaner_test, replace=False)
                        final_outlier_CCleaner_test = n_outlier_CCleaner_test - len(remove_idx_CCleaner_test)
                        print("CCleaner anomalies test", final_outlier_CCleaner_test)
                        
                        #5
                        mn_Cobalt_test = n_outlier_Cobalt_test 
                        remove_idx_Cobalt_test= rng.choice(outlier_Cobalt_indices_test, mn_Cobalt_test, replace=False)
                        final_outlier_Cobalt_test = n_outlier_Cobalt_test - len(remove_idx_Cobalt_test)
                        print("Cobalt anomalies test", final_outlier_Cobalt_test)
                        
                        #6
                        mn_Downware_test = n_outlier_Downware_test - 739
                        remove_idx_Downware_test = rng.choice(outlier_Downware_indices_test,  mn_Downware_test, replace=False)
                        final_outlier_Downware_test = n_outlier_Downware_test - len(remove_idx_Downware_test)
                        print("Downware anomalies test", final_outlier_Downware_test)
                        
                        #7 
                        mn_Dridex_test= n_outlier_Dridex_test - 739
                        remove_idx_Dridex_test = rng.choice(outlier_Dridex_indices_test,  mn_Dridex_test, replace=False)
                        final_outlier_Dridex_test = n_outlier_Dridex_test - len(remove_idx_Dridex_test)
                        print("Dridex anomalies", final_outlier_Dridex_test)
                        
                        #8
                        mn_Emotet_test = n_outlier_Emotet_test - 739
                        remove_idx_Emotet_test = rng.choice(outlier_Emotet_indices_test,  mn_Emotet_test, replace=False)
                        final_outlier_Emotet_test = n_outlier_Emotet_test - len(remove_idx_Emotet_test)
                        print("Emotet anomalies test", final_outlier_Emotet_test)
                          
                        #9
                        mn_HTBot_test = n_outlier_HTBot_test - 739
                        remove_idx_HTBot_test = rng.choice(outlier_HTBot_indices_test,  mn_HTBot_test, replace=False)
                        final_outlier_HTBot_test = n_outlier_HTBot_test - len(remove_idx_HTBot_test)
                        print("HTBot anomalies test", final_outlier_HTBot_test)
                        
                        #10
                        mn_MagicHound_test = n_outlier_MagicHound_test - 739
                        remove_idx_MagicHound_test = rng.choice(outlier_MagicHound_indices_test,  mn_MagicHound_test, replace=False)
                        final_outlier_MagicHound_test = n_outlier_MagicHound_test - len(remove_idx_MagicHound_test)
                        print("MagicHound anomalies", final_outlier_MagicHound_test)
                        
                        #11
                        mn_MinerTrojan_test = n_outlier_MinerTrojan_test - 739
                        remove_idx_MinerTrojan_test = rng.choice(outlier_MinerTrojan_indices_test,  mn_MinerTrojan_test, replace=False)
                        final_outlier_MinerTrojan_test = n_outlier_MinerTrojan_test - len(remove_idx_MinerTrojan_test)
                        print("MinerTrojan anomalies test", final_outlier_MinerTrojan_test)
                        
                        #12
                        mn_PUA_test = n_outlier_PUA_test  - 739
                        remove_idx_PUA_test = rng.choice(outlier_PUA_indices_test, mn_PUA_test, replace=False)
                        final_outlier_PUA_test  = n_outlier_PUA_test  - len(remove_idx_PUA_test)
                        print("PUA anomalies", final_outlier_PUA_test)
                        
                        #13
                        #mn_Ramnit_test = n_outlier_Ramnit_test - 272
                        mn_Ramnit_test = n_outlier_Ramnit_test
                        remove_idx_Ramnit_test = rng.choice(outlier_Ramnit_indices_test,  mn_Ramnit_test, replace=False)
                        final_outlier_Ramnit_test = n_outlier_Ramnit_test - len(remove_idx_Ramnit_test)
                        print("Ramnit anomalies", final_outlier_Ramnit_test)
            
                        #14
                        #mn_Sality_test = n_outlier_Sality_test - args.known_outliers
                        mn_Sality_test = n_outlier_Sality_test
                        remove_idx_Sality_test = rng.choice(outlier_Sality_indices_test,  mn_Sality_test, replace=False)
                        final_outlier_Sality_test = n_outlier_Sality_test - len(remove_idx_Sality_test)
                        print("Sality anomalies", final_outlier_Sality_test)
                        
                        #15
                        mn_Tinba_test = n_outlier_Tinba_test - 739
                        #mn_Tinba_test = n_outlier_Tinba_test
                        remove_idx_Tinba_test = rng.choice(outlier_Tinba_indices_test,  mn_Tinba_test, replace=False)
                        final_outlier_Tinba_test = n_outlier_Tinba_test - len(remove_idx_Tinba_test)
                        print("Tinba anomalies test", final_outlier_Tinba_test)
                        
                        #16
                        mn_TrickBot_test = n_outlier_TrickBot_test - 739
                        remove_idx_TrickBot_test = rng.choice(outlier_TrickBot_indices_test,  mn_TrickBot_test, replace=False)
                        final_outlier_TrickBot_test = n_outlier_TrickBot_test - len(remove_idx_TrickBot_test)
                        print("TrickBotanomalies test", final_outlier_TrickBot_test)
                        
                        #17
                        mn_Trickster_test = n_outlier_Trickster_test - 739
                        remove_idx_Trickster_test = rng.choice(outlier_Trickster_indices_test,  mn_Trickster_test, replace=False)
                        final_outlier_Trickster_test = n_outlier_Trickster_test - len(remove_idx_Trickster_test)
                        print("Trickster anomalies", final_outlier_Trickster_test)
                        
                        #18
                        mn_TrojanDownloader_test = n_outlier_TrojanDownloader_test - 739
                        remove_idx_TrojanDownloader_test = rng.choice(outlier_TrojanDownloader_indices_test,  mn_TrojanDownloader_test, replace=False)
                        final_outlier_TrojanDownloader_test = n_outlier_TrojanDownloader_test - len(remove_idx_TrojanDownloader_test)
                        print("TrojanDownloader anomalies", final_outlier_TrojanDownloader_test)
                        
                        #19
                        mn_Ursnif_test = n_outlier_Ursnif_test - 739
                        remove_idx_Ursnif_test = rng.choice(outlier_Ursnif_indices_test,  mn_Ursnif_test, replace=False)
                        final_outlier_Ursnif_test = n_outlier_Ursnif_test - len(remove_idx_Ursnif_test)
                        print("Ursnif anomalies", final_outlier_Ursnif_test)
                        
                        #20
                        mn_WebCompanion_test = n_outlier_WebCompanion_test - 739
                        remove_idx_WebCompanion_test = rng.choice(outlier_WebCompanion_indices_test,  mn_WebCompanion_test, replace=False)
                        final_outlier_WebCompanion_test = n_outlier_WebCompanion_test - len(remove_idx_WebCompanion_test)
                        print("WebCompanion anomalies", final_outlier_WebCompanion_test)
                        
                        remove_idx_test = np.concatenate([remove_idx_Adload_test,remove_idx_Artemis_test,remove_idx_BitCoinMiner_test,remove_idx_CCleaner_test,remove_idx_Cobalt_test,remove_idx_Downware_test,remove_idx_Dridex_test,remove_idx_Emotet_test,remove_idx_HTBot_test,remove_idx_MagicHound_test,remove_idx_MinerTrojan_test,remove_idx_PUA_test,remove_idx_Ramnit_test,remove_idx_Sality_test,remove_idx_Tinba_test,remove_idx_TrickBot_test,remove_idx_Trickster_test,remove_idx_TrojanDownloader_test,remove_idx_Ursnif_test,remove_idx_WebCompanion_test])
                        
                        x_test = np.delete(x_test, remove_idx_test, axis=0)
                        y_test = np.delete(y_test, remove_idx_test, axis=0)    
                        
                    noises = inject_noise(outliers, n_noise, random_seed)
                    print("noises shape", noises.shape)
                    x_train = np.append(x_train, noises, axis=0)
                    y_train = np.append(y_train, np.zeros((noises.shape[0], 1)))
    
                else:
                    if n_outliers > args.known_outliers:
                        mn = n_outliers - args.known_outliers
                        remove_idx = rng.choice(outlier_indices, mn, replace=False)
                        retain_idx = set(np.arange(x_train.shape[0])) - set(remove_idx)
                        retain_idx = list(retain_idx)
                        x_train = x_train[retain_idx]
                        y_train = y_train[retain_idx]
    
                    noises = inject_noise_sparse(outliers, n_noise, random_seed)
                    x_train = vstack([x_train, noises])
                    y_train = np.append(y_train, np.zeros((noises.shape[0], 1)))
    
                outlier_indices = np.where(y_train == 1)[0]
                inlier_indices = np.where(y_train == 0)[0]
            
                outlier_Adload_indices = np.where(attack_Adload_train == 1)[0]
                
                outlier_Artemis_indices = np.where(attack_Artemis_train == 1)[0]
                
                outlier_BitCoinMiner_indices = np.where(attack_BitCoinMiner_train == 1)[0]
                
                outlier_CCleaner_indices = np.where(attack_CCleaner_train == 1)[0]
                
                outlier_Cobalt_indices = np.where(attack_Cobalt_train == 1)[0]
                
                outlier_Downware_indices = np.where(attack_Downware_train == 1)[0]
                
                outlier_Dridex_indices = np.where(attack_Dridex_train == 1)[0]
                
                outlier_Emotet_indices = np.where(attack_Emotet_train == 1)[0]
                
                outlier_HTBot_indices = np.where(attack_HTBot_train == 1)[0]
                
                outlier_MagicHound_indices = np.where(attack_MagicHound_train == 1)[0]
                
                outlier_MinerTrojan_indices = np.where(attack_MinerTrojan_train == 1)[0]
                
                outlier_PUA_indices = np.where(attack_PUA_train == 1)[0]
                
                outlier_Ramnit_indices = np.where(attack_Ramnit_train == 1)[0]
                
                outlier_Sality_indices = np.where(attack_Sality_train == 1)[0]
                
                outlier_Tinba_indices = np.where(attack_Tinba_train == 1)[0]
                
                outlier_TrickBot_indices = np.where(attack_TrickBot_train == 1)[0]
                
                outlier_Trickster_indices = np.where(attack_Trickster_train == 1)[0]
                
                outlier_TrojanDownloader_indices = np.where(attack_TrojanDownloader_train == 1)[0]
                
                outlier_Ursnif_indices = np.where(attack_Ursnif_train == 1)[0]
                
                outlier_WebCompanion_indices = np.where(attack_WebCompanion_train == 1)[0]
                
            
                print('training samples num:', y_train.shape[0],
                      'outlier num:', outlier_indices.shape[0],
                      'inlier num:', inlier_indices.shape[0],
                      'noise num:', n_noise)
                print('training samples num:', y_train.shape[0],
                      'outlier num:', outlier_indices.shape[0],
                      'inlier num:', inlier_indices.shape[0])
                n_samples_trn = x_train.shape[0]
                inlier_number = len(inlier_indices)
                n_outliers = len(outlier_indices)
                print("Training data size: %d, No. outliers: %d" % (x_train.shape[0], n_outliers))
    
                start_time = time.time()
                input_shape = x_train.shape[1:]
                print('input_shape', input_shape)
                
                print('x_train shape', x_train.shape)
    
                print('x_test shape', x_test.shape)
                print('y_train shape', y_train.shape)
                print('y_test shape', y_test.shape)
            
                epochs = args.epochs
                batch_size = args.batch_size
                nb_batch = args.nb_batch
    
                model = deviation_network(input_shape, network_depth)
                print(model.summary())
                model_filename= filename + "_" + str(args.cont_rate) + "cr_"  + str(args.batch_size) +"bs_" + str(args.known_outliers) + "ko_" + str(network_depth) +"d.h5" 
                model_name = os.path.join('./model/devnet_', model_filename)
                checkpointer = ModelCheckpoint(filepath=model_name, monitor='loss', verbose=0,
                                               save_best_only=True, save_weights_only=True)
          
                model.fit_generator(batch_generator_sup(x_train, outlier_indices, inlier_indices,outlier_Adload_indices, outlier_Artemis_indices, outlier_BitCoinMiner_indices, outlier_CCleaner_indices, outlier_Cobalt_indices, outlier_Downware_indices, outlier_Dridex_indices, outlier_Emotet_indices, outlier_HTBot_indices, outlier_MagicHound_indices, outlier_MinerTrojan_indices, outlier_PUA_indices, outlier_Ramnit_indices, outlier_Sality_indices, outlier_Tinba_indices, outlier_TrickBot_indices, outlier_Trickster_indices, outlier_TrojanDownloader_indices, outlier_Ursnif_indices, outlier_WebCompanion_indices, opt, batch_size, nb_batch, rng),
                                              steps_per_epoch = nb_batch,
                                              epochs = epochs,
                                              callbacks=[checkpointer]) 
        
                
                train_time += time.time() - start_time
    
                start_time = time.time()
                
                scores = load_model_weight_predict(model_name, input_shape, network_depth, x_test)
    
                test_time += time.time() - start_time
                
                rauc[i], ap[i] = aucPerformance_norm(scores, y_test)

                #CALCULATION F1 SCORE OFFICIAL
                preds = scores
                #class_one = preds > 0.5
                class_one = preds > 2
                predic_class = np.where(class_one == True,1,0)
                
                precision_new = precision_score(y_test, predic_class)
                print('Precision',precision_new)
                recall_new = recall_score(y_test, predic_class)
                print('Recall',recall_new)
                f1_new = 2 * ((precision_new * recall_new) / (precision_new + recall_new ))
                print('F1 new',f1_new)
                precision, recall, thresh = precision_recall_curve(y_test, preds)
                
                fig3 = plt.figure()
                plt.plot(model.history.history['loss'])
                plt.title('model loss')
                plt.ylabel('loss')
                plt.xlabel('epoch')
                plt.show()
                fig3.savefig('my_figure3.png')
                
                
                fig = plt.figure()
                plt.plot(thresh, precision[:-1], 'b--', label='precision')
                plt.plot(thresh, recall[:-1], 'g--', label = 'recall')
                plt.xlabel('Threshold')
                plt.legend(loc='upper right')
                plt.ylim([0,1])
                fig.savefig('my_figure.png')
                
                fig2 = plt.figure()
                plt.plot(recall, precision)
                # axis labels
                plt.xlabel('Recall')
                plt.ylabel('Precision')

                fig2.savefig('my_figure2.png')
                
                f1 = 2 * ((precision * recall) / (precision + recall ))
                max_precision = precision[np.argmax(f1)]
                max_recall = recall[np.argmax(f1)]
                print('max precision', max_precision)
                print('max recall', max_recall)
                f_one = 2 * ((max_precision * max_recall) / (max_precision + max_recall ))
                print('f1', f_one)    
                
                architecture = '25/5'
                losses = 'devloss'
                #losses = 'binarycross'
                supervision = 'weakly_know_10'
                writeResults(filename,supervision,architecture,epochs,batch_size,nb_batch,losses,final_outlier_Adload,final_outlier_Artemis,final_outlier_BitCoinMiner,final_outlier_CCleaner,final_outlier_Cobalt, final_outlier_Downware, final_outlier_Dridex, final_outlier_Emotet,final_outlier_HTBot, final_outlier_MagicHound, final_outlier_MinerTrojan, final_outlier_PUA, final_outlier_Ramnit, final_outlier_Sality, final_outlier_Tinba, final_outlier_TrickBot, final_outlier_Trickster, final_outlier_TrojanDownloader, final_outlier_Ursnif, final_outlier_WebCompanion,rauc[i], ap[i], precision_new, recall_new, f1_new,n_samples_trn,n_outliers,inlier_number,n_noise,train_time,max_precision, max_recall, f_one, path="./results/performanceNetMl.csv")
  

        mean_auc = np.mean(rauc)
        std_auc = np.std(rauc)
        mean_aucpr = np.mean(ap)
        std_aucpr = np.std(ap)
        train_time = train_time / runs
        test_time = test_time / runs
        print("average AUC-ROC: %.4f, average AUC-PR: %.4f" % (mean_auc, mean_aucpr))
        print("STD AUC-ROC: %.4f, STD AUC-PR: %.4f" % (std_auc,  std_aucpr))
        print("average runtime: %.4f seconds" % (train_time + test_time))
    


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--network_depth", choices=['2', '4'], default='2',
                        help="the depth of the network architecture")
    parser.add_argument("--batch_size", type=int, default=512, help="batch size used in SGD")
    parser.add_argument("--nb_batch", type=int, default=20, help="the number of batches per epoch")
    parser.add_argument("--epochs", type=int, default=50, help="the number of epochs")
    parser.add_argument("--runs", type=int, default=1,
                        help="how many times we repeat the experiments to obtain the average performance")
    parser.add_argument("--known_outliers", type=int, default=8,
                        help="the number of labeled outliers available at hand")
    parser.add_argument("--cont_rate", type=float, default=0.0,
                        help="the outlier contamination rate in the training data")
    parser.add_argument("--input_path", type=str, default='./dataset/', help="the path of the data sets")
    parser.add_argument("--data_set", type=str, default='annthyroid_21feat_normalised', help="a list of data set names")
    parser.add_argument("--data_format", choices=['0', '1'], default='0',
                        help="specify whether the input data is a csv (0) or libsvm (1) data format")
    parser.add_argument("--output", type=str,
                        default='./results/devnet_auc_performance_30outliers_0.02contrate_2depth_10runs.csv',
                        help="the output file path")
    parser.add_argument("--ramdn_seed", type=int, default=42, help="the random seed number")
    args = parser.parse_args()
    run_devnet(args)
    