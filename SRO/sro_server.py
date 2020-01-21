from flask import Flask, request
import requests as req
import pdb
from werkzeug.utils import secure_filename
from osmotic_orchestrator import get_aggreated_metrics_file
import os
import sys
import shutil
from redis import Redis
from threading import Thread, Timer
import pandas as pd
from datetime import datetime
import time

import cloud_slice
import config
import pathlib
from slice_flavor import SliceFlavor

UPLOAD_FOLDER = 'slices_files'
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def files_flavor_directory(slice_id, flavor_id):
  slice_directory = 'slice_{}'.format(slice_id)
  flavor_directory = 'flavor_{}'.format(flavor_id)
  directory = os.path.join(app.config['UPLOAD_FOLDER'], slice_directory)
  directory = os.path.join(directory, flavor_directory)
  pathlib.Path(directory).mkdir(parents=True, exist_ok=True)

  return directory

cloud_slice = cloud_slice.CloudSlice(sla_metric_name = 'R_99')
flavor1 = SliceFlavor(id = 1, cloud_slice = cloud_slice, bandwidth='10Mbit')
flavor2 = SliceFlavor(id = 2, cloud_slice = cloud_slice, bandwidth='30Mbit')
flavor1.upgrade_flavor = flavor2
flavor2.downgrade_flavor = flavor1

cloud_slice.flavors = [flavor1, flavor2]

cloud_slice.lower_bound_sla = 30
cloud_slice.upper_bound_sla = 180

cloud_slice.lower_predictions_limit=1
cloud_slice.upper_predictions_limit=1

flavor1.directory = files_flavor_directory(flavor1.cloud_slice.id, flavor1.id)
flavor2.directory = files_flavor_directory(flavor2.cloud_slice.id, flavor2.id)

flavor1.x_file = os.path.join(flavor1.directory, 'x_selected_metrics.csv')
flavor1.y_file = os.path.join(flavor1.directory, 'y_metrics.csv')

flavor2.x_file = os.path.join(flavor2.directory, 'x_selected_metrics.csv')
flavor2.y_file = os.path.join(flavor2.directory, 'y_metrics.csv')

hosts = ['192.168.0.107', '192.168.0.108', '192.168.0.109', '192.168.0.113', '192.168.0.116']
flavor1.hosts = hosts
flavor2.hosts = hosts

flavor1.load_forecast_model()
flavor2.load_forecast_model()

cloud_slice.current_flavor=flavor1

ALLOWED_EXTENSIONS=['csv']

def allowed_file(filename):
  return '.' in filename and \
          filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# request creation of a learning model from the slice usage
@app.route('/slice/<int:slice_id>/flavor/<int:flavor_id>/profile', methods=['POST'])
def profile_flavor(slice_id, flavor_id):
  end_user_file = request.files['file']
  if 'file' not in request.files:
    return 'No file sent.', 300

  if not end_user_file or end_user_file.filename == '':
    return 'No selected file', 300

  sla_metric_name = request.args.get('sla_metric_name', None)
  timestamp_field = request.args.get('timestamp_label', None)
  url_to_answer = request.args.get('url_to_answer', None)

  if allowed_file(end_user_file.filename) and sla_metric_name and timestamp_field:
    fields = [timestamp_field, sla_metric_name]
    filtered_file = pd.read_csv(end_user_file,usecols=fields)
    directory = files_flavor_directory(slice_id, flavor_id)
    local_filename = os.path.join(directory, 'y_metrics.csv' )
    filtered_file.to_csv(index=False, path_or_buf=local_filename)
    flavor = None

    if flavor_id == 1:
      flavor = flavor1
    else:
      flavor = flavor2

    flavor.y_file = local_filename
    cloud_slice.sla_metric_name = sla_metric_name

    t = Thread(target=get_aggreated_metrics_file, args=(flavor,))
    t.start()

    return 'Creation of model Accepted. We will notify you on %s after model creation. ' \
      % url_to_answer, 201
  else:
    return 'file %s is not able to be processed.' % end_user_metrics_file, 301

@app.route('/slice/<int:slice_id>/flavor/<int:flavor_id>/profilling_metrics', methods=['POST'])
def profilling_metrics_flavor(slice_id, flavor_id):
  config.logger.info('Infrastructure metrics of slice {} received for flavor'.format(slice_id, flavor_id))
  x_selected_file = request.files['x_selected']
  timeserie_map_file = request.files['timeserie_map']

  if not x_selected_file or x_selected_file.filename == '' or not timeserie_map_file or timeserie_map_file.filename == '':
    return 'No file sent', 300

  if allowed_file(x_selected_file.filename) and allowed_file(timeserie_map_file.filename):
    directory = files_flavor_directory(slice_id, flavor_id)
    x_selected_file_local_filename = os.path.join(directory, 'x_selected_metrics.csv')
    x_selected_file.save(x_selected_file_local_filename)
    flavor = None

    if flavor_id == 1:
      flavor = flavor1
    else:
      flavor = flavor2

    flavor.x_file = x_selected_file_local_filename
    flavor.y_file = os.path.join(directory, 'y_metrics.csv')

    t = Thread(target=flavor.create_forecast_model)
    t.start()
    return 'File Received ', 200
  else:
    return 'File %s was received but was not able to be processed. Please check file name and size.' % end_user_metrics_file, 301

@app.route('/slice/<int:slice_id>/start_sla_forecast', methods=['POST'])
def start_sla_forecast(slice_id):
  t = Thread(target=cloud_slice.start_sla_forecast)
  t.start()
  return 'Starting forecast ', 200

@app.route('/slice/<int:slice_id>/upgrade', methods=['POST'])
def upgrade(slice_id):
  t = Thread(target=cloud_slice.require_elasticity, args=('upgrade',))
  t.start()
  return 'Upgrading slice flavor', 200

@app.route('/slice/<int:slice_id>/downgrade', methods=['POST'])
def downgrade(slice_id):
  t = Thread(target=cloud_slice.require_elasticity, args=('downgrade',))
  t.start()
  return 'Downgrading slice flavor', 200

@app.route('/slice/<int:slice_id>/start_orchestration', methods=['POST'])
def start_orchestration(slice_id):
  t = Thread(target=cloud_slice.start_orchestration)
  t.start()
  return 'Starting orchestration ', 200

if __name__=='__main__':
  app.run(debug=True, host=config.SRO_SERVER_HOST, port='13131')
