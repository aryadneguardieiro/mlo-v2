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

def create_dir(path):
    try:  
        shutil.rmtree(path)
    except OSError:
        print("Directory not deleted")
    try:
        os.mkdir(path)
    except OSError:  
        print("Error at the creation of directory")
        sys.exit(1)

def plot_figure(fig, ax, measure_name, file_name):
  handles, labels = ax.get_legend_handles_labels()
  lgd = ax.legend(handles, loc='upper center', bbox_to_anchor=(0.5,-0.1))
  ax.grid(True)
  xfmt = md.DateFormatter('%H:%M:%S')
  ax.xaxis.set_major_formatter(xfmt)
  ax.xaxis_date()
  pyplot.xticks( rotation=25 )
  pyplot.title(measure_name)
  fig.savefig(file_name, bbox_extra_artists=(lgd,), bbox_inches='tight')
  pyplot.close(fig)

if len(sys.argv) != 3:
  print('Usage: {0} cvs_dir_path plot_dir_path'.format(sys.argv[0]))
  sys.exit(1)

cvs_dir_path = sys.argv[1]
csv_list = glob.glob(cvs_dir_path+"/*.csv")
plot_dir_path = sys.argv[2]

#bar = ChargingBar('Processando graficos', max=len(csv_list), suffix = '%(percent).1f%% %(elapsed_td)s')
create_dir(plot_dir_path)
metrics_counter = 0
print("Numer of metrics: " + str(len(csv_list)))

for csv_file_name in csv_list:
  with open(csv_file_name) as csv_file:
    reader = csv.DictReader(csv_file)
    time_series = {}

    for row in reader:
      value = float(row.pop('value'))
      timestamp = datetime.datetime.fromtimestamp((float(row.pop('timestamp'))))
      tag = '-'.join(list(row.values())[1:])

      if tag in time_series:
        time_series[tag]['x'].append(timestamp)
        time_series[tag]['y'].append(value)
      else:
        time_series[tag] = {'x': [timestamp], 'y': [value]}

    fig = pyplot.figure()
    ax = pyplot.subplot(111)
    
    cont = 1
    qtd_legend = 0
    measure_name = csv_file_name.split('/')[-1]
    measure_name = measure_name[:-4]
    for time_serie_name, time_serie_value in time_series.items():
      #pdb.set_trace()
      ax.plot(time_serie_value['x'],time_serie_value['y'], label = time_serie_name)
      qtd_legend = qtd_legend + 1
      if qtd_legend == 10:
        qtd_legend = 0
        plot_figure(fig, ax, measure_name, plot_dir_path + '/' + measure_name + '_' + csv_file_name.split('/')[-2] + '_' + str(cont) + '.png')
        cont = cont + 1
        fig = pyplot.figure()
        ax = pyplot.subplot(111)

    plot_figure(fig, ax, measure_name, plot_dir_path + '/' + measure_name + '_' + csv_file_name.split('/')[-2] + '_' + str(cont) + '.png')
    #bar.next()
    metrics_counter = metrics_counter + 1
    print("Printed metrics: "+ str(metrics_counter))  
#bar.finish()


 
