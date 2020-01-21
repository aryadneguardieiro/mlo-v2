import csv
import glob
import sys
import datetime
import pdb 

if len(sys.argv) != 5:
  print('Usage: {0} cvs_dir_path y_file_name y_column_name output_file_name'.format(sys.argv[0]))
  sys.exit(1)

cvs_dir_path = sys.argv[1]
csv_list = glob.glob(cvs_dir_path+"/*.csv")
y_file_name = sys.arg[2]
y_column_name = sys.arg[3]
output_file_name = sys.argv[4]

file_counters = 0
print("Numer of files to be processed: " + str(len(csv_list)))

with open('output_file_name.csv', 'w', newline='') as output_file:
  spamwriter = csv.writer(output_file)



  spamwriter.writerow(['Spam'] * 5 + ['Baked Beans'])


  with open(y_file_name) as y_file:
    reader = csv.DictReader(csv_file)



for csv_file_name in csv_list:
  with open(csv_file_name) as csv_file:
    reader = csv.DictReader(csv_file)


    for row in reader:
      value = float(row.pop('value'))
      timestamp = datetime.datetime.fromtimestamp((float(row.pop('timestamp'))))
      tag = '-'.join(list(row.values())[1:])