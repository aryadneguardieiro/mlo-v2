
$DESCRIPTION="single vm test 30 5,10,15 clients, restrition 2Mbit burst 10Kb lat 400.0ms, --adaptive-logic=nearoptimal "
$SERVICE_IP="http://192.168.0.124:31313"

#client execution
ssh 192.168.0.112 /bin/bash << EOF
  timeout 30m ./vlc/bin/vlc -vv --loop --adaptive-logic=nearoptimal  ${DESCRIPTION}:31313/pl_30fps-1-v3-gustavo.xspf
  ./logs/dropbox_log_sender.sh framesDisplayedCalc "${DESCRIPTION}" mix_periodic_11-01-19.sh
EOF

#load generator execution
python loadgen/new-loadgen.py -v -l playlists/pl_30fps-1-v4.xspf -s 5,10 30 10

#prometheus csv extraction 
python3 extract_csv_from_prometheus_splited_files_single_thread.py http://192.168.0.120:30000 30m ~/teste_aryadne 01/01/19 23:30:00 1
aggregate.sh
filter_timestamp.sh
