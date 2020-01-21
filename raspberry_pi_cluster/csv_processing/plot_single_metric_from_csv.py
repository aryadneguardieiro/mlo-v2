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

if len(sys.argv) != 4:
  print('Usage: {0} cvs_dir_path plot_dir_path metric_name'.format(sys.argv[0]))
  sys.exit(1)

cvs_dir_path = sys.argv[1]
csv_list = glob.glob(cvs_dir_path+"/*.log")
csv_list = csv_list + glob.glob(cvs_dir_path+"/*.csv")
plot_dir_path = sys.argv[2]
metric_name = sys.argv[3]

for csv_file_name in csv_list:
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
    file_name = os.path.join(plot_dir_path,metric_name + '_' + os.path.basename(csv_file_name).split('.')[0] + '.png')
    fig.savefig(file_name, bbox_extra_artists=(lgd,), bbox_inches='tight')
    pyplot.close(fig)