import time
import Constants
import pandas as pd
import numpy as np
import Constants
import pdb
import csv
import hashlib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.feature_selection import SelectKBest, f_classif
from SliceConfig import metricsChosen
from collections import OrderedDict

def executeFeatureSelection(yField, K, sliceId, currentTimestamp, metricsInfo, sliceFlavor, path):
  sliceIdAsString = str(sliceId)
  fields     = ['timestamp', yField]
  xRaw       = pd.read_csv(path+'/XFileProcessed{0}.csv'.format(currentTimestamp))
  yRaw       = pd.read_csv(path+'/YFileProcessed{0}.csv'.format(currentTimestamp), skipinitialspace=True, usecols=fields)

  listXRaw = list(xRaw)
  metricsSelectedInfo = dict()

  if not metricsChosen[sliceId][sliceFlavor]:
    selector = SelectKBest(f_classif, k=int(K))
    _ = selector.fit_transform(xRaw, yRaw[yField])
    idxSelected = selector.get_support(indices=True)

    metrics = ['timestamp'] + [listXRaw[metric] for metric in idxSelected]
    metricsChosen[sliceId][sliceFlavor] = list(metricsSelectedInfo.values())

    for metric in idxSelected:
      metricHashId = listXRaw[metric]
      rawMetric = metricsInfo[metricHashId]
      metricsSelectedInfo[metricHashId] = rawMetric

  else:
    metricsChosenHashes = []
    for metric in metricsChosen[sliceId][sliceFlavor]:
      metricItems = metric.items()
      orderedLabels = OrderedDict(sorted(metricItems, key=lambda t: t[0]))
      hashObject = hashlib.sha1(str(orderedLabels).encode())
      timeSerieHashId = hashObject.hexdigest()
      metricsChosenHashes.append(timeSerieHashId)
      metricsSelectedInfo[timeSerieHashId] = metric

    metrics = ['timestamp'] + metricsChosenHashes

  dataFrame = pd.DataFrame(xRaw[metrics])
  dataFrame.to_csv(path + '/XSelected{0}.csv'.format(currentTimestamp) , index=False)

  print("Metrics chosen for flavor: ", sliceFlavor, " = ", metricsChosen[sliceId][sliceFlavor])

  pathToTranslator = path + '/metricsSelectedTranslator{0}.csv'.format(currentTimestamp)

  with open(pathToTranslator, 'w') as metricsSelectedFile:
    metricsWriter = csv.writer(metricsSelectedFile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
    metricsWriter.writerow(['metricHash', 'metricInfo'])
    for key, value in metricsSelectedInfo.items():
      metricsWriter.writerow([key, value])
  return True
