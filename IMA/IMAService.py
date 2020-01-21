from flask import jsonify
from ExtractPrometheus import extractPrometheus
from SliceConfig import slicesConfig, metricsChosen
from FeatureSelect import executeFeatureSelection
from threading import Thread
from datetime import datetime
from YAMLHandler import doConfigMapYml
import Constants
import pdb
import os
import subprocess
import requests
import time
import json

class IMAService(Thread):

  def __init__(self, sliceId, callbackURL, K, YField, currentTimestamp, sliceFlavor, executePrometheus, path):
    Thread.__init__(self)
    self.sliceId = sliceId
    self.callbackURL = callbackURL
    self.K = K
    self.YField = YField
    self.currentTimestamp = currentTimestamp
    self.sliceFlavor = sliceFlavor
    self.executePrometheus = executePrometheus
    self.path = path

  def run(self):
    sliceId = self.sliceId
    sliceIdAsString = str(sliceId)
    callbackURL = self.callbackURL
    K = self.K
    currentTimestamp = self.currentTimestamp
    sliceFlavor = self.sliceFlavor
    executePrometheus = self.executePrometheus
    path = self.path

    YFileName = '/YFile{0}.csv'.format(currentTimestamp)
    pathToY = path + YFileName
    YFile = open(pathToY, "r")
    promURL = slicesConfig[sliceId - 1].get('promURL')

    try:
      YField = self.YField
      if not YField:
        YField = YFile.readline().split(",")[1]
      else:
        YFile.readline()

      firstTimestamp = int(YFile.readline().split(',')[0])
      YFile.close()
      if executePrometheus:
        lastTimestamp = int(str(subprocess.check_output(['tail', '-1', pathToY]).decode(Constants.DECODE_PATTERN)).split(",")[0])

        duration = lastTimestamp - firstTimestamp + 1

        beginDate = datetime.fromtimestamp(firstTimestamp)
        XAggregated = "/XFileAggregated{0}.csv".format(currentTimestamp)
        step = 1 if duration < 5 else 5
        for i in range(6, duration):
          if duration % i == 0:
            step = i
            break
        print("Will divide requests to prometheus in ", step, " steps.")
        print("Starting to extract data from prometheus. The experiment lasts " + str(duration) + " seconds.")
        metricsInfo = extractPrometheus(promURL, duration, 's', sliceIdAsString, beginDate, step, path, currentTimestamp)
        print("End of extraction of prometheus data.")
        with open(path + XAggregated, "w") as xfile:
          print("Starting to aggregate X metrics into one file.")
          if subprocess.call(['aggregate ' + path + Constants.PROM_DATA], stdout=xfile, shell=True) == 0:
            xfile.close()
          else:
            raise Exception("Error in aggregating X metrics")
        print("Starting to filter timestamps of X and Y metrics.")
        if subprocess.call(['filter_timestamp ' + path + ' ' + YFileName[1:] + ' ' + XAggregated[1:] + ' ' + str(currentTimestamp)], shell=True) != 0:
          raise Exception("Error in filtering timestamps")
      else:
        metricsInfo = self.readMetricsFile(path, currentTimestamp)

      print("Starting to execute feature selection")
      if executeFeatureSelection(YField, K, sliceId, currentTimestamp, metricsInfo, sliceFlavor, path):
        print("Sending Xselected to SRO")
        files = {'timeserie_map' : open(path + '/metricsSelectedTranslator{0}.csv'.format(currentTimestamp), 'rb'), 'x_selected' : open(path + '/XSelected{0}.csv'.format(currentTimestamp), 'rb')}
        response = requests.post(url = callbackURL, stream = True, files = files)

        if response.status_code != 200:
          raise Exception("Error in sending X file to requester")
        else:
          print("Ok, everythings fine.")
    except Exception as e:
      raise e

  def readMetricsFile(self, path, currentTimestamp):
    metricsFileName = path + "/metricsTranslator{0}.csv".format(currentTimestamp)
    metricsInfo = {}
    with open(metricsFileName, 'r') as csvFile:
      csvFile.readline() #cabecalho
      lines = csvFile.readlines()
      for line in lines:
        comaPos = line.find(',')
        if comaPos != -1:
          metricHash = line[0:comaPos]
          metricInfo = json.loads(line[comaPos + 2:-2].replace("'", "\""))
          metricsInfo[metricHash] = metricInfo

    return metricsInfo

  @staticmethod
  def sendNewConfigMap(sliceId, sliceFlavor, path):
    print("Preparing config-map file to prometheus 2")
    doConfigMapYml(sliceId, metricsChosen[sliceId][sliceFlavor], path)
    files = {'configMap' : open(path + '/config-map.yaml', 'rb')}
    response = requests.post(url = Constants.KUBERNETES_MASTER_URL, stream = True, files = files)
    if response.status_code != 200:
      raise Exception("Error in sending config-map file to kubernetes master")
    return True

  @staticmethod
  def createDir(path):
    if not os.path.exists(path):
      try:
        os.mkdir(path)
      except:
        raise Exception("Failed to create diretory {0}".format(path))
