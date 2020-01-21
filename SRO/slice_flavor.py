import pdb
import os.path
import numpy as np
from necos_forecast import NeuralNetworkModel
from collections import deque
import cloud_slice
import subprocess
import pickle
import time

class SliceFlavor:
  def __init__(self, id=1, downgrade_flavor = None, upgrade_flavor = None, bandwidth = None, 
    hosts = None, cloud_slice = None, x_file = None, y_file = None, forecast_strategy='neural_network',
    directory = None):
    self.id = id
    self.x_file = x_file
    self.y_file = y_file
    self.hosts = hosts
    self.forecast_strategy = forecast_strategy
    self.downgrade_flavor = downgrade_flavor #cassandra hosts
    self.upgrade_flavor = upgrade_flavor
    self.cloud_slice = cloud_slice
    self.directory = directory
    self.metrics_window = None
    self.regressor = None
    self.regressor_file = 'regressor_file.sav'
    self.bandwidth = bandwidth
    self.flavor_features = None
    self.full_window = 0

  def infrastructure_metrics_hash(self):
    if self.regressor != None:
      return self.regressor.x_features
    raise ValueError("Regressor not initialized")

  def create_empty_window(self):
    self.metrics_window = deque()
    rows, columns  = self.regressor.input_shape
    for i in range(0, rows):
      self.metrics_window.append(np.zeros(columns))
    self.full_window = 0

  def load_forecast_model(self):
    if self.regressor == None:
      self.regressor = NeuralNetworkModel(self.x_file, self.y_file,
          self.cloud_slice.sla_metric_name, directory = self.directory)
      self.regressor.load_model()
      self.create_empty_window()

  def create_forecast_model(self):
    if self.forecast_strategy == 'neural_network':
      self.regressor = NeuralNetworkModel(self.x_file, self.y_file,
        self.cloud_slice.sla_metric_name, directory = self.directory, steps_in_future=30,evaluation_interval = 200)
      self.regressor.create_model()
      self.flavor_features = self.regressor.x_features
    else:
      message = 'Forecast strategy {} not implemented.'.format(self.forecast_strategy)
      log_sro_info(message)
      raise ValueError(message)
    self.create_empty_window()

  def change_flavor(self, new_flavor):
    self.update_bandwidth("del", self.bandwidth, self.hosts)
    self.update_bandwidth("add", new_flavor.bandwidth, new_flavor.hosts)

    if self.cloud_slice:
      self.cloud_slice.elasticity_callback(new_flavor)

  def request_upgrade(self):
    self.change_flavor(self.upgrade_flavor)

  def request_downgrade(self):
    self.change_flavor(self.downgrade_flavor)

  def update_bandwidth(self, operation, bandwidth, hosts):
    for host in hosts:
      if bandwidth != '':
        command = 'scripts/apply_bandwidth_operation.sh {} {} {}'.format(operation, host, bandwidth)
        subprocess.call([command], shell=True)

  def add_window(self,current_measurements):
    ordered_labels = sorted(current_measurements.keys())
    current_measurements = [float(current_measurements[key]) for key in ordered_labels]
    current_measurements = np.asarray(current_measurements)
    self.metrics_window.append(current_measurements)
    self.metrics_window.popleft()
    self.full_window = self.full_window + 1

  def is_full_window(self):
    return self.full_window >= self.regressor.input_shape[0]

  def first_window_full(self):
    return self.full_window == self.regressor.input_shape[0]

  def forecast_kpi(self, current_measurements, timestamp):
    self.add_window(current_measurements)
    metrics_array = np.asarray(self.metrics_window)
    metrics_array = metrics_array.reshape(1, metrics_array.shape[0], metrics_array.shape[1])
    forecast_timestamp = timestamp + self.regressor.steps_in_future
    return forecast_timestamp, self.regressor.forecast(metrics_array)

  def upgrade_flavor(self):
    return upgrade_flavor

  def downgrade_flavor(self):
    return downgrade_flavor

if __name__ == '__main__':
  # c = cloud_slice.CloudSlice(sla_metric_name = 'W_95')
  # directory = 'slices_files/slice_1/flavor_1'
  # x_file = os.path.join(directory, 'x_selected_metrics.csv')
  # y_file = os.path.join(directory, 'y_metrics.csv')
  hosts = ['192.168.0.107', '192.168.0.108', '192.168.0.109', '192.168.0.113', '192.168.0.116']  
  bandwidth1='10Mbit'
  bandwidth2='30Mbit'
  op = 'add'
  flavor1 = SliceFlavor()
  num_exp = 10
  for width in ['10Mbit', '30Mbit']:
    time_exp = 0
    for i in range(0, num_exp):
      before = time.time()
      flavor1.update_bandwidth('add',width,hosts)
      flavor1.update_bandwidth('del', width, hosts)
      after = time.time()
      time_exp = time_exp + after - before
    time_exp = time_exp/num_exp
    print("Bandwidth: {}, average time spent: {}".format(width, time_exp))
