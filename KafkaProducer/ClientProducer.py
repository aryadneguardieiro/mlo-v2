import pdb
import csv
import sys
from os import path
from time import sleep

from kafka import KafkaProducer

class ClientProducer():

  def normalizeLine(self, line):
    if not line or line == '':
      return line
    return line.replace('\n', '').strip()

  def isEmpty(self, line):
    return not line or line == ''

  def clientProducer(self, topicName, csvFullPathFile, testDuration, slaMetricName, sliceId, tableName):
    if not path.exists(csvFullPathFile):
      print("File does not exist. Please, check file.")
      exit(1)

    producer = KafkaProducer(bootstrap_servers=['n1-kafka-zookeeper:9092','n2-kafka-zookeeper:9092', 'n3-kafka-zookeeper:9092'])

    currentTimestamp = 0
    firstTimestamp = 0
    timestampPos = 0
    slaMetricPos = 0
    countEmpty = 0

    slaMetricValue = 0.0

    stop = False

    lastPos = None
    header = None

    while not stop:
      with open(csvFullPathFile, 'r') as csvFile:
        sleep(2)
        if lastPos:
          csvFile.seek(lastPos)
        else:
          header = csvFile.readline().replace('\n', '').split(',')
          try:
            timestampPos = header.index('timestamp')
            slaMetricPos = header.index(slaMetricName)
          except:
            print("Didnt found header: 'timestamp' or '" + slaMetricName + "'. Please, check file.")
            exit(2)

        lines = csvFile.readlines()
        lastPos = csvFile.tell()
        for line in lines:
          line = self.normalizeLine(line)
          if self.isEmpty(line):
            countEmpty = countEmpty + 1
            if countEmpty == 3:
              stop = True
            break

          clientslaMetricName = line.split(',')
          if clientslaMetricName != None and timestampPos < len(clientslaMetricName) and clientslaMetricName[timestampPos] != '':
            currentTimestamp = int(clientslaMetricName[timestampPos])
            slaMetricValue = float(clientslaMetricName[slaMetricPos])
            if firstTimestamp == 0:
              firstTimestamp = currentTimestamp
            clientslaMetricNameMessage = self.buildKafkaMessage(tableName, slaMetricValue, currentTimestamp, sliceId)
            producer.send(topicName, clientslaMetricNameMessage)
            print('Sent ' + str(currentTimestamp) + ' to Kafka')
            if testDuration > 0 and currentTimestamp - firstTimestamp + 1 >= testDuration:
              producer.close()
              stop = True
              break

  def buildKafkaMessage(self, tableName, clientslaMetricValue, timestamp, sliceId):
    message = '{{ "measurement": "{}_{}", "values": [{}], "time": "{}", "tags": {{}} }}' \
      .format(tableName, sliceId, clientslaMetricValue, timestamp)
    return str.encode(message)

if __name__ == "__main__":
  if len(sys.argv) != 7:
    print("Usage: python3 ClientProducer.py topic_name csv_full_path_file test_duration sla_metric_name slice_id table_name")
  else:
    topicName = sys.argv[1]
    csvFullPathFile = sys.argv[2]
    testDuration = int(sys.argv[3])
    slaMetricName = sys.argv[4]
    sliceId = int(sys.argv[5])
    tableName = sys.argv[6]
    ClientProducer().clientProducer(topicName, csvFullPathFile, testDuration, slaMetricName, sliceId, tableName)
