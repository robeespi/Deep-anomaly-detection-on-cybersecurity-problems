# Malware Detection and Neural Networks

Due to constantly changing specifications, the malware detection system demands constant compliance activities to meet ever-evolving security requirements.
Neural Networks models have showed their ability to perform feature extraction from raw data. This type of algorithms seek to exploit the unknown structure in the input distribution in order to discover intermediate feature representations to downstream tasks. In this work, a neural network approach is implemented to identify malware

# Weakly supervised settings 
In this settings, we have some labels for anomaly classes, but the labels for some anomalies classes are incomplete in the training stage. During the test stage, we have evenly distributed anomalies classes under sampled by the minority class. Two major challenges are how to learn expressive normality/abnormality representations with a small amount of labeled anomaly data and how to learn detection models that are generalized well as anomalies uncovered by the given labeled anomaly data

# Results
![alt text](https://github.com/robeespi/Weakly-Supervised-Malware-Detection/blob/main/performance%20weakly%20supervised.jpeg)

This repository uses a binary cross entropy as a empirical loss function, you can refer to the deviation Loss function in this following paper
https://arxiv.org/pdf/1911.08623.pdf


