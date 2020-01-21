#!/bin/bash

if [ $# -ne 1 ]; then
	echo "Usage: aggregate csv_directory"
	exit 1
fi

timeinsec=$(date +%s)

directory=$1

cd $directory

qtdFiles=$(ls | grep csv$ | wc -l);

echo "timestamp,"$(ls | grep csv$ | sort | sed s/\.csv//g) | sed s/\ /,/g;

#escolhe um arquivo para comecar
file_name=$(ls | grep csv$ | head -1);


#percorre as linhas do arquivo escolhido, vendo quais timestamps presentes neste arquivo também estão em todos os outros
#os timestamps que nao pertencerem a este arquivo ou que nao estiverem presentes em todos os demais serão excluidos
for timestamp in $(tail -n +2 $file_name | cut -d',' -f1); do
	grep -r "^$timestamp" > /tmp/grepXFiles$timeinsec
	qtd=$(cat /tmp/grepXFiles$timeinsec | wc -l);

	if [ $qtd -eq $qtdFiles ]; then
		echo $timestamp,$(cat /tmp/grepXFiles$timeinsec | sort | cut -d ',' -f 2 | sed s/\\r//g) | sed s/' '/,/g;
	fi
done;
rm /tmp/grepXFiles$timeinsec
exit 0
