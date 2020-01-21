import requests
import config
import pdb
import subprocess

NUMBER_OF_METRICS = 15

def request_ima_monitoring(flavor):
  endpoint = config.IMA_ELASTICITY_ENDPOINT.replace('slice_id', str(flavor.cloud_slice.id))
  endpoint = endpoint.replace('flavor_id', str(flavor.id))
  try:
    response = requests.post(url = endpoint)

    if response.status_code == 400:
      config.logger.info('Can not reach IMA')

  except Exception as e:
    config.logger.info('Exception {} during request {}'.format(e, config.IMA_METRICS_ENDPOINT))

def get_aggreated_metrics_file(flavor):
  callback = config.SERVER_RECEIVE_AGGREATED_METRICS_URL.replace('slice_id', str(flavor.cloud_slice.id))
  callback = callback.replace('flavor_id', str(flavor.id))

  data = {'callbackURL': callback, \
            'K': NUMBER_OF_METRICS, \
            'YField': flavor.cloud_slice.sla_metric_name, \
            'sliceFlavor': flavor.id}

  files = {'YFile': open(flavor.y_file,'rb')}
  try:
    config.logger.info('Requesting infrastructure metrics to IMA')
    response = requests.post(url = config.IMA_METRICS_ENDPOINT + str(flavor.cloud_slice.id), data = data, stream=True, files=files)

    if response.status_code == 400:
      config.logger.info('Can not reach IMA')

  except Exception as e:
    config.logger.info('Exception {} during request {}'.format(e, config.IMA_METRICS_ENDPOINT))

#if __name__ == '__main__':
  #cloud_slice = CloudSlice()
  #update_bandwith(cloud_slice)
  #get_aggreated_metrics_file(1, '/home/aryadne/projects/elasticity-demo-ufu/slice_files/1_y_metrics.csv', 'W_95', config.SERVER_RECEIVE_AGGREATED_METRICS_URL)

