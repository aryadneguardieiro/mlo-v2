#!/bin/bash

email_list=$1
log_dir=$2
plot_dir=$3

last_modified_file = $(ls $log_dir -t1 |  head -n 1)
python3 plot_single_file.py last_modified_file
last_created_figure = $(ls -t1 |  head -n 1)


mail -s "Resultados do ultimo experimento" -a $last_modified_file -a $last_created_figure $email_list