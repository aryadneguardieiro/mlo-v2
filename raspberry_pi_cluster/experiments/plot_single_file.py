import csv
import glob
import sys
import os # mkdir 
import shutil # rmtree
import matplotlib
import datetime
matplotlib.use('agg')
import pdb 
from matplotlib import pyplot
from matplotlib import rcParams
#rcParams.update({'figure.autolayout': True})
#from progress.bar import ChargingBar
rcParams['legend.fontsize'] = 'small'
import matplotlib.dates as md

if len(sys.argv) != 3:
  print('Usage: {0} cvs_file metric_name'.format(sys.argv[0]))
  sys.exit(1)

csv_file_name = sys.argv[1]
metric_name = sys.argv[2]

with open(csv_file_name) as csv_file:
  reader = csv.DictReader(csv_file)
  time_serie = {'x': [], 'y': []}

  for row in reader:
    value = float(row.pop(metric_name))
    timestamp = datetime.datetime.fromtimestamp((float(row.pop('timestamp'))))
    time_serie['x'].append(timestamp)
    time_serie['y'].append(value)

  fig = pyplot.figure(figsize=(20, 2))
  ax = pyplot.subplot(111)
  ax.plot(time_serie['x'],time_serie['y'], label = metric_name)
  handles, labels = ax.get_legend_handles_labels()
  lgd = ax.legend(handles, loc='upper center', bbox_to_anchor=(0.5,-0.1))
  ax.grid(True)
  xfmt = md.DateFormatter('%H:%M:%S')
  ax.xaxis.set_major_formatter(xfmt)
  pyplot.ylim(0, 40)
  ax.xaxis_date()
  pyplot.xticks( rotation=25 )
  pyplot.title(metric_name)
  file_name = os.path.join(metric_name + '.png')
  fig.savefig(file_name, bbox_extra_artists=(lgd,), bbox_inches='tight')
  pyplot.close(fig)