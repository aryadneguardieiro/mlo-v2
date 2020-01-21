import pandas as pd
import numpy as np
import config
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.feature_selection import SelectKBest, f_classif
import pdb
import random
import time
from kafka import KafkaConsumer, KafkaProducer
import kafka
import json
from collections import OrderedDict
import hashlib
from joblib import dump, load
from datetime import datetime
import time
import os.path

from necos_forecast import NeuralNetworkModel
import osmotic_orchestrator
import slice_flavor

class CloudSlice:
  def __init__(self, id=1, kafka_topics='', current_flavor = None, flavors=[], 
    lower_bound_sla = None, upper_bound_sla = None, orchestration_active = False,
    sla_metric_name = '', lower_predictions_limit = 1, upper_predictions_limit = 1):
    self.id = id
    self.kafka_topics = kafka_topics
    self.consumer = None
    self.producer = None
    self.kafka_servers = ['n1-kafka-zookeeper:9092', 'n3-kafka-zookeeper:9092']
    self.consumer_topic = 'selected-metrics-5'
    self.producer_topic = 'sro-sla-estimations'
    self.ignore_metrics = ['scrape_duration_seconds', 'scrape_samples_post_metric_relabeling', 'scrape_samples_scraped', 'up']
    self.flavors = flavors
    self.current_flavor = current_flavor
    self.lower_predictions_limit = lower_predictions_limit
    self.upper_predictions_limit = upper_predictions_limit
    self.sla_metric_name = sla_metric_name
    self.orchestration_active = orchestration_active
    self.forecast_active = False
    self.sro_log_kafka_topic = 'sro-slice-1-log'
    self.upper_bound_sla = upper_bound_sla
    self.lower_bound_sla = lower_bound_sla
    self.doing_elasticity = False
    self.reset_prediction_counters()

  def set_id(self, id):
    self.id = id

  def set_final_endpoint(self, endpoint):
    self.final_endpoint = endpoint

  def set_kafka_topics(self, topics):
    self.kafka_topics = topics

  def convert_str_to_date_time(self, data_string):
    return datetime.strptime(data_string,'%Y-%m-%dT%H:%M:%SZ')

  def set_current_prediction_timestamp(self, data_string):
    self.current_prediction_timestamp = self.convert_str_to_date_time(data_string)

  def reset_current_prediction_timestamp(self):
    date_now = datetime.now()
    self.set_current_prediction_timestamp(datetime.strftime(date_now,'%Y-%m-%dT%H:%M:%SZ'))

  def produce_sro_log_kafka(self, message):
  #[{"measurement": "measurement_name", "values":[0], "time":1436372292, "tags": {"tag1": "value1"}}]
    self.reset_current_prediction_timestamp()
    msg = '{{ "measurement": "sro_slice_{}_logs", "values": [], "time": "{}", "tags": {{"message": message}} }}' \
     .format(self.id, self.current_prediction_timestamp.timestamp()+5)
    msg = str.encode(msg)
    self.producer.send(self.sro_log_kafka_topic, msg)

  def log_sro_info(self, message):
    config.logger.info(message)
    #self.produce_sro_log_kafka(message)

  def start_orchestration(self):
    self.log_sro_info('Activating orchestration tools')
    self.orchestration_active = True
    if not self.forecast_active:
      self.start_sla_forecast()

  def start_producer(self):
    if self.producer == None:
      self.producer = kafka.KafkaProducer(bootstrap_servers=self.kafka_servers)

  def start_consumer(self):
    self.reset_current_prediction_timestamp()
    self.current_measurements = {}

    if self.consumer == None:
      self.consumer = kafka.KafkaConsumer(bootstrap_servers=self.kafka_servers,\
        #auto_offset_reset='earliest',\
        consumer_timeout_ms=100000,\
        #enable_auto_commit=False,\
        value_deserializer=lambda m: json.loads(m.decode('utf-8')))
      self.consumer.subscribe([self.consumer_topic])

  def start_sla_forecast(self):
    self.log_sro_info('Loading flavor_{} ({}) forecast model'.format(self.current_flavor.id, self.current_flavor.bandwidth))
    self.current_flavor.load_forecast_model()
    if not self.forecast_active:
      self.log_sro_info('Requesting IMA to collect slice selected metrics')
      osmotic_orchestrator.request_ima_monitoring(self.current_flavor)
      self.forecast_active = True
      self.log_sro_info('Starting Kafka producer and consumer')
      self.start_consumer()
      self.start_producer()
      self.log_sro_info('Starting KPI forecast')
      for message in self.consumer:
        self.ingest(message)

  def is_relevant_metric(self,value):
    try:
      if value['labels']['__name__'] in self.ignore_metrics:
        return False, ""

      items = value['labels'].items()
      orderedLabels = OrderedDict(sorted(items, key=lambda t: t[0]))
      hash_object = hashlib.sha1(str(orderedLabels).encode())
      time_serie_hash_id = hash_object.hexdigest()

      return time_serie_hash_id in self.relevant_metrics_hash(), time_serie_hash_id
    except KeyError:
      config.logger.error("Expecting that value had labels")

    return False, ""

  def is_completed_current_measurements(self):
    for hash_id in self.relevant_metrics_hash():
      if hash_id not in self.current_measurements:
        return False

    return True

  def relevant_metrics_hash(self):
    return self.current_flavor.infrastructure_metrics_hash()

  def produce_kafka_message(self, sla_value, prediction_timestamp):
    # [{"measurement": "measurement_name", "values":[0], "time":1436372292, "tags": {"tag1": "value1"}}]
    msg = '{{ "measurement": "sla_slice_{}_estimations", "values": [{}], "time": "{}", "tags": {{}} }}' \
      .format(self.id, sla_value, prediction_timestamp)
    msg = str.encode(msg)
    self.producer.send(self.producer_topic, msg)

  def ingest(self, message):
    time_serie_meassurement = message.value
    message_timestamp = self.convert_str_to_date_time(time_serie_meassurement['timestamp'])
    is_relevant_metric, metric_hash = self.is_relevant_metric(time_serie_meassurement)
    #self.log_sro_info('Processing kafka message')

    if is_relevant_metric:
      if self.current_prediction_timestamp == message_timestamp:
        self.current_measurements[metric_hash] = time_serie_meassurement['value']
      elif self.current_prediction_timestamp < message_timestamp:
        self.current_measurements = {metric_hash: time_serie_meassurement['value']}
        self.current_prediction_timestamp = message_timestamp

    if self.is_completed_current_measurements():
      forecast_timestamp, sla_value = self.current_flavor.forecast_kpi(self.current_measurements, self.current_prediction_timestamp.timestamp())
      self.produce_kafka_message(sla_value, forecast_timestamp)
      self.current_measurements = {}

      if self.orchestration_active:
        self.analyse_kpi(sla_value)

  def reset_prediction_counters(self):
    self.upper_predictions = 0
    self.lower_predictions = 0

  def elasticity_callback(self, new_flavor):
    self.doing_elasticity = False
    new_flavor.metrics_window = self.current_flavor.metrics_window
    new_flavor.full_window = self.current_flavor.full_window
    self.current_flavor = new_flavor
    self.log_sro_info("Elasticity completed")
    #self.log_sro_info("Triggering IMA changes")
    #osmotic_orchestrator.request_ima_monitoring(self.current_flavor)
    #self.start_sla_forecast()

  def require_elasticity(self, operation):
    if operation == 'downgrade':
      if self.current_flavor.downgrade_flavor:
        self.doing_elasticity = True
        self.log_sro_info("Requesting elasticity downgrade")
        self.current_flavor.request_downgrade()
        self.reset_prediction_counters()
      else:
        self.log_sro_info("Downgrade flavor requested but current flavor does not allow")
    if operation == 'upgrade':
      if self.current_flavor.upgrade_flavor:
        self.doing_elasticity = True
        self.log_sro_info("Requesting elasticity upgrade.")
        self.current_flavor.request_upgrade()
        self.reset_prediction_counters()
      else:
        self.log_sro_info("Upgrade flavor requested but current flavor does not allow")

  def analyse_kpi(self, forecasted_kpi):
    if self.current_flavor.first_window_full():
      self.log_sro_info("Metrics window is now full. Scalling actions may be applied")
    if not self.doing_elasticity and self.current_flavor.is_full_window():
      if forecasted_kpi >= self.upper_bound_sla:
        self.upper_predictions = self.upper_predictions + 1
        if self.upper_predictions >= self.upper_predictions_limit:
          self.require_elasticity('upgrade')
      elif forecasted_kpi <= self.lower_bound_sla:
        self.lower_predictions = self.lower_predictions + 1
        if self.lower_predictions >= self.lower_predictions_limit:
          self.require_elasticity('downgrade')
    elif self.current_flavor.full_window == 1:
      self.log_sro_info("Metrics window is being fulfilled. Unprecise predictions can be made")

  def estimate_kpi(self):
    return self.current_flavor.forecast_kpi(self.current_measurements)

# if __name__ == '__main__':
#   cloud_slice = CloudSlice()
#   cloud_slice.start_producer()
#   cloud_slice.produce_sro_log_kafka("Test Log")

  #cloud_slice = CloudSlice(sla_metric_name= 'W_95',\
  #  x_file='slice_files/1_x_selected_metrics.csv', \
  #  y_file='slice_files/1_y_metrics.csv', \
  #  kafka_topics='prometheus_metrics')

  #cloud_slice.train_model()
  # cloud_slice = CloudSlice()
  # cloud_slice.start_producer()
  # while True:
  #   time.sleep(1)
  #   cloud_slice.produce_kafka_message(random.randint(0,60), datetime.now())

  # c = CloudSlice(sla_metric_name = 'W_95',
  # lower_bound_sla=11, upper_bound_sla=20,
  # lower_predictions_limit = 1,
  # upper_predictions_limit = 1)

  # directory = 'slices_files/slice_1/flavor_1'
  # x_file = os.path.join(directory, 'x_selected_metrics.csv')
  # y_file = os.path.join(directory, 'y_metrics.csv')

  # flavor = slice_flavor.SliceFlavor(
  #     id = 1,
  #     bandwidth = "10Mbit",
  #     hosts = ['192.168.0.107', '192.168.0.108', '192.168.0.109', '192.168.0.113', '192.168.0.116'],
  #     x_file = x_file,
  #     y_file = y_file,
  #     directory = directory,
  #     cloud_slice=c)

  # #flavor.create_forecast_model()

  # flavor2 = slice_flavor.SliceFlavor(
  #     id = 2,
  #     bandwidth = "20Mbit",
  #     hosts = ['192.168.0.107', '192.168.0.108', '192.168.0.109', '192.168.0.113', '192.168.0.116'],
  #     x_file = x_file,
  #     y_file = y_file,
  #     directory = directory,
  #     cloud_slice=c)

  # flavor.upgrade_flavor = flavor2
  # flavor2.downgrade_flavor = flavor

  # c.current_flavor = flavor2
  # c.analyse_kpi(9)
