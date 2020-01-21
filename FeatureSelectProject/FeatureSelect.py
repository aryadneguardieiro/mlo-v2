import time
import Constants
import pandas as pd
import numpy as np
import Constants
import pdb
import csv
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.feature_selection import SelectKBest, f_classif

def executeFeatureSelection(yField, K, sliceId, currentTimestamp, metricsInfo):
  path        = Constants.SLICE_FILES_DIR + Constants.SLICE_DIR_NAME + sliceId
  fields      = ['timestamp', yField]
  xRaw       = pd.read_csv(path+'/XFileProcessed{0}.csv'.format(currentTimestamp))
  yRaw       = pd.read_csv(path+'/YFileProcessed{0}.csv'.format(currentTimestamp), skipinitialspace=True, usecols=fields)

  selector = SelectKBest(f_classif, k=int(K))
  _ = selector.fit_transform(xRaw, yRaw[yField])
  idxSelected = selector.get_support(indices=True)

  listXRaw = list(xRaw)
  metrics = ['timestamp'] + [listXRaw[metric] for metric in idxSelected]
  dataFrame = pd.DataFrame(xRaw[metrics])
  dataFrame.to_csv(path_or_buf = Constants.SLICE_FILES_DIR + Constants.SLICE_DIR_NAME + sliceId + '/XSelected{0}.csv'.format(currentTimestamp) , index=False)

  print("Selected Metrics Info:")
  metricsSelectedInfo = dict()
  for metric in idxSelected:
    metricHashId = listXRaw[metric]
    metricsSelectedInfo[metricHashId] = metricsInfo[listXRaw[metric]]
    print(metricsInfo[listXRaw[metric]])

  path = Constants.SLICE_FILES_DIR + Constants.SLICE_DIR_NAME + str(sliceId) + '/metricsSelectedTranslator{0}.csv'.format(currentTimestamp)

  with open(path, 'w') as metricsSelectedFile:
    metricsWriter = csv.writer(metricsSelectedFile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
    metricsWriter.writerow(['metricHash', 'metricInfo'])
    for key, value in metricsSelectedInfo.items():
      metricsWriter.writerow([key, value])
  return list(metricsSelectedInfo.values())
