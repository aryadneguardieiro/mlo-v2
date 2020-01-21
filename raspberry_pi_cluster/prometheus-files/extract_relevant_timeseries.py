import numpy as np
from collections import OrderedDict
from operator import itemgetter
import sys
import glob
from progress.bar import ChargingBar
import csv
import datetime

def group_time_series(csv_file_name):
  timeseries = {}

  with open(csv_file_name) as csv_file:
    reader = csv.DictReader(csv_file)

    for row in reader:
      value = float(row.pop('value'))
      timestamp = datetime.datetime.fromtimestamp((float(row.pop('timestamp'))))
      tag = '-'.join(list(row.values()))

      if tag in timeseries:
        timeseries[tag]['x'].append(timestamp)
        timeseries[tag]['y'].append(value)
      else:
        timeseries[tag] = {'x': [timestamp], 'y': [value]}

  return timeseries

def calc_timeseries_variances(timeseries_variances, timeseries):
  for timeserie_name, timeserie_value in timeseries.items():
    variance = np.var(timeserie_value['y'])
    if variance > 0:
      timeseries_variances[timeserie_name] = variance

  return timeseries_variances

def main(args):
  if len(args) != 2:
    print('Usage: {0} cvs_dir_path'.format(args[0]))
    sys.exit(1)

  cvs_dir_path = args[1]
  csv_list = glob.glob(cvs_dir_path+"/*.csv")
  csv_list = list(filter(lambda x: "_sum" not in x and "bucket" not in x and "count" not in x, csv_list))

  bar = ChargingBar('Processando arquivos', max=len(csv_list), suffix = '%(percent).1f%% %(elapsed_td)s')

  timeseries_variances = {}

  for csv_file_name in csv_list:
    timeseries = group_time_series(csv_file_name)
    calc_timeseries_variances(timeseries_variances, timeseries)
    bar.next()

  bar.finish()

  print("\n Metricas ordenadas por variancia: ")
  sorted_dic = OrderedDict(sorted(timeseries_variances.items(), key = itemgetter(1), reverse = True))


  for item in sorted_dic.items():
    print(item)

if __name__ == '__main__':
  main(sys.argv)