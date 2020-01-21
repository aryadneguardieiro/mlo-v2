from __future__ import print_function
import csv
import requests
import sys
import os # mkdir
import shutil # rmtree
import pdb
import math
import time
import hashlib
import traceback
import Constants
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from functools import reduce
from collections import OrderedDict

# code based on:
# https://www.robustperception.io/prometheus-query-results-as-csv and
# https://medium.com/@aneeshputtur/export-data-from-prometheus-to-csv-b19689d780aa


def extractPrometheus(prometheusUrl, duration, timeUnity, sliceId, beginTestDayHour, step, path, currentTimestamp):
  destinationDirPath = path + Constants.PROM_DATA

  createDir(destinationDirPath)
  start = beginTestDayHour
  durationInSec = duration * getFormatInSeconds(timeUnity)
  startFormated, endFormated = formatStartEndTime(start, timedelta(seconds=durationInSec))
  metricNames = getMetrixNames(prometheusUrl)
  metricsToGet = ["go_gc_duration_seconds", "go_goroutines", "go_info", "go_memstats_alloc_bytes", "go_memstats_alloc_bytes_total", "go_memstats_buck_hash_sys_bytes", "go_memstats_frees_total", "go_memstats_gc_cpu_fraction", "go_memstats_gc_sys_bytes", "go_memstats_heap_alloc_bytes", "go_memstats_heap_idle_bytes", "go_memstats_heap_inuse_bytes", "go_memstats_heap_objects", "go_memstats_heap_released_bytes", "go_memstats_heap_sys_bytes", "go_memstats_last_gc_time_seconds", "go_memstats_lookups_total", "go_memstats_mallocs_total", "go_memstats_mcache_inuse_bytes", "go_memstats_mcache_sys_bytes", "go_memstats_mspan_inuse_bytes", "go_memstats_mspan_sys_bytes", "go_memstats_next_gc_bytes", "go_memstats_other_sys_bytes", "go_memstats_stack_inuse_bytes", "go_memstats_stack_sys_bytes", "go_memstats_sys_bytes", "go_threads", "node_arp_entries", "node_boot_time_seconds", "node_context_switches_total", "node_cpu_guest_seconds_total", "node_cpu_seconds_total", "node_disk_io_now", "node_disk_io_time_seconds_total", "node_disk_io_time_weighted_seconds_total", "node_disk_read_bytes_total", "node_disk_read_time_seconds_total", "node_disk_reads_completed_total", "node_disk_reads_merged_total", "node_disk_write_time_seconds_total", "node_disk_writes_completed_total", "node_disk_writes_merged_total", "node_disk_written_bytes_total", "node_entropy_available_bits", "node_exporter_build_info", "node_filefd_allocated", "node_filefd_maximum", "node_filesystem_avail_bytes", "node_filesystem_device_error", "node_filesystem_files", "node_filesystem_files_free", "node_filesystem_free_bytes", "node_filesystem_readonly", "node_filesystem_size_bytes", "node_forks_total", "node_intr_total", "node_load1", "node_load15", "node_load5", "node_memory_Active_anon_bytes", "node_memory_Active_bytes", "node_memory_Active_file_bytes", "node_memory_AnonHugePages_bytes", "node_memory_AnonPages_bytes", "node_memory_Bounce_bytes", "node_memory_Buffers_bytes", "node_memory_Cached_bytes", "node_memory_CmaFree_bytes", "node_memory_CmaTotal_bytes", "node_memory_CommitLimit_bytes", "node_memory_Committed_AS_bytes", "node_memory_DirectMap1G_bytes", "node_memory_DirectMap2M_bytes", "node_memory_DirectMap4k_bytes", "node_memory_Dirty_bytes", "node_memory_HardwareCorrupted_bytes", "node_memory_HugePages_Free", "node_memory_HugePages_Rsvd", "node_memory_HugePages_Surp", "node_memory_HugePages_Total", "node_memory_Hugepagesize_bytes", "node_memory_Inactive_anon_bytes", "node_memory_Inactive_bytes", "node_memory_Inactive_file_bytes", "node_memory_KernelStack_bytes", "node_memory_Mapped_bytes", "node_memory_MemAvailable_bytes", "node_memory_MemFree_bytes", "node_memory_MemTotal_bytes", "node_memory_Mlocked_bytes", "node_memory_NFS_Unstable_bytes", "node_memory_PageTables_bytes", "node_memory_SReclaimable_bytes", "node_memory_SUnreclaim_bytes", "node_memory_Shmem_bytes", "node_memory_Slab_bytes", "node_memory_SwapCached_bytes", "node_memory_SwapFree_bytes", "node_memory_SwapTotal_bytes", "node_memory_Unevictable_bytes", "node_memory_VmallocChunk_bytes", "node_memory_VmallocTotal_bytes", "node_memory_VmallocUsed_bytes", "node_memory_WritebackTmp_bytes", "node_memory_Writeback_bytes", "node_netstat_Icmp6_InErrors", "node_netstat_Icmp6_InMsgs", "node_netstat_Icmp6_OutMsgs", "node_netstat_Icmp_InErrors", "node_netstat_Icmp_InMsgs", "node_netstat_Icmp_OutMsgs", "node_netstat_Ip6_InOctets", "node_netstat_Ip6_OutOctets", "node_netstat_IpExt_InOctets", "node_netstat_IpExt_OutOctets", "node_netstat_Ip_Forwarding", "node_netstat_TcpExt_ListenDrops", "node_netstat_TcpExt_ListenOverflows", "node_netstat_TcpExt_SyncookiesFailed", "node_netstat_TcpExt_SyncookiesRecv", "node_netstat_TcpExt_SyncookiesSent", "node_netstat_Tcp_ActiveOpens", "node_netstat_Tcp_CurrEstab", "node_netstat_Tcp_InErrs", "node_netstat_Tcp_PassiveOpens", "node_netstat_Tcp_RetransSegs", "node_netstat_Udp6_InDatagrams", "node_netstat_Udp6_InErrors", "node_netstat_Udp6_NoPorts", "node_netstat_Udp6_OutDatagrams", "node_netstat_UdpLite6_InErrors", "node_netstat_UdpLite_InErrors", "node_netstat_Udp_InDatagrams", "node_netstat_Udp_InErrors", "node_netstat_Udp_NoPorts", "node_netstat_Udp_OutDatagrams", "node_network_address_assign_type", "node_network_carrier", "node_network_carrier_changes_total", "node_network_device_id", "node_network_dormant", "node_network_flags", "node_network_iface_id", "node_network_iface_link", "node_network_iface_link_mode", "node_network_mtu_bytes", "node_network_name_assign_type", "node_network_net_dev_group", "node_network_protocol_type", "node_network_receive_bytes_total", "node_network_receive_compressed_total", "node_network_receive_drop_total", "node_network_receive_errs_total", "node_network_receive_fifo_total", "node_network_receive_frame_total", "node_network_receive_multicast_total", "node_network_receive_packets_total", "node_network_speed_bytes", "node_network_transmit_bytes_total", "node_network_transmit_carrier_total", "node_network_transmit_colls_total", "node_network_transmit_compressed_total", "node_network_transmit_drop_total", "node_network_transmit_errs_total", "node_network_transmit_fifo_total", "node_network_transmit_packets_total", "node_network_transmit_queue_length", "node_network_up", "node_procs_blocked", "node_procs_running", "node_scrape_collector_duration_seconds", "node_scrape_collector_success", "node_sockstat_FRAG_inuse", "node_sockstat_FRAG_memory", "node_sockstat_RAW_inuse", "node_sockstat_TCP_alloc", "node_sockstat_TCP_inuse", "node_sockstat_TCP_mem", "node_sockstat_TCP_mem_bytes", "node_sockstat_TCP_orphan", "node_sockstat_TCP_tw", "node_sockstat_UDPLITE_inuse", "node_sockstat_UDP_inuse", "node_sockstat_UDP_mem", "node_sockstat_UDP_mem_bytes", "node_sockstat_sockets_used", "node_textfile_scrape_error", "node_time_seconds", "node_timex_estimated_error_seconds", "node_timex_frequency_adjustment_ratio", "node_timex_loop_time_constant", "node_timex_maxerror_seconds", "node_timex_offset_seconds", "node_timex_pps_calibration_total", "node_timex_pps_error_total", "node_timex_pps_frequency_hertz", "node_timex_pps_jitter_seconds", "node_timex_pps_jitter_total", "node_timex_pps_shift_seconds", "node_timex_pps_stability_exceeded_total", "node_timex_pps_stability_hertz", "node_timex_status", "node_timex_sync_status", "node_timex_tai_offset_seconds", "node_timex_tick_seconds", "node_uname_info", "node_vmstat_pgfault", "node_vmstat_pgmajfault", "node_vmstat_pgpgin", "node_vmstat_pgpgout", "node_vmstat_pswpin", "node_vmstat_pswpout", "process_cpu_seconds_total", "process_max_fds", "process_open_fds", "process_resident_memory_bytes", "process_start_time_seconds", "process_virtual_memory_bytes", "process_virtual_memory_max_bytes", "promhttp_metric_handler_requests_in_flight", "promhttp_metric_handler_requests_total"]
  metricsInfo = {}
  metricsInfoFileName = path + "/metricsTranslator{0}.csv".format(currentTimestamp)

  for metricName in metricNames:
    if metricName not in metricsToGet:
      continue
    try:
      timeSeries = getMetricTimeSeries(prometheusUrl, metricName, startFormated, endFormated)

      for _, timeSerie in enumerate(timeSeries):
        results = requestTimeSerieValues(prometheusUrl, timeSerie, start, durationInSec, step)

        if 'result' in results and len(results['result']) > 0:
          result = results['result'][0]
        else:
          raise Exception("result with unknown format: {0}".format(str(results)))

        if 'metric' in result and 'values' in result and len(result['values']) > 0: 
          firstValue=result['values'][0][1]
          printValues=False

          for value in result['values']:
            if value[1] != firstValue:
                printValues=True
                break

          if printValues:
            metricInfo = result['metric']
            metricsItems = metricInfo.items()

            orderedLabels = OrderedDict(sorted(metricsItems, key=lambda t: t[0]))
            hashObject = hashlib.sha1(str(orderedLabels).encode())
            timeSerieHashId = hashObject.hexdigest()
            metricsInfo[timeSerieHashId] = metricInfo

            file_name = timeSerieHashId + '.csv'
            file_name = destinationDirPath + '/' + file_name

            with open(str(file_name), 'w') as csvfile:
              writer = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
              writer.writerow(['timestamp', 'value'])

              for value in result['values']:
                writer.writerow(value)
    except Exception as e:
      raise e
  with open(str(metricsInfoFileName), 'w') as csvfile:
    writer = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(['metricHash', 'metricInfo'])
    for key, value in metricsInfo.items():
      writer.writerow([key, value])

  return metricsInfo


def formatStartEndTime(start, shiftTime):
  offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
  offset = offset / (-3600)
  offsetFormatted = '.000' + convertToHourFormat(offset)
  endTestDate = start + shiftTime
  startFormated = start.isoformat() + offsetFormatted
  endFormated = endTestDate.isoformat() + offsetFormatted
  return startFormated, endFormated

def makeRequest(url, errorMessage, params={}):
  response = requests.get(url, params=params, timeout=120)
  data = response.json()['data']

  if not response or response.status_code != 200 or data == None:
    raise Exception(errorMessage + "\nURL: " + url + "\nParams: " + str(params) + "\nReponse: " + str(response))

  return data

def requestTimeSerieValues(url, timeSerie, start, durationInSec, step):
  endpoint = '{0}/api/v1/query_range'.format(url)
  metricName = timeSerie.pop('__name__')
  prometheusQuery = createPromQuery(metricName, timeSerie)
  startPart = start
  end = start + timedelta(seconds=durationInSec)
  stop = False
  shiftTime = timedelta(seconds=int(durationInSec / step))
  oneMilliSecond = timedelta(seconds=1)
  data = None
  valuesList = None
  while not stop:
    endPart = startPart + shiftTime
    if endPart >= end:
      endPart = end
      stop = True
    startPartFormated, endPartFormated = formatStartEndTime(startPart, shiftTime)
    params = {'query': prometheusQuery, 'start': startPartFormated, 'end': endPartFormated, 'step' : Constants.STEP_PROMETHEUS}
    stepData = makeRequest(endpoint, "It wasn't possible to retrive time serie values", params)
    if not data:
      data = stepData
      valuesList = data['result'][0]['values']
    else:
      valuesList = valuesList + stepData['result'][0]['values']
    startPart = endPart + oneMilliSecond
  data['result'][0]['values'] = valuesList
  return data

def createPromQuery (metricName, timeSerie):
  prometheusQuery = ""
  for label, value in timeSerie.items():
    pair = label.replace("'","") + "=" + '"' + value + '"'
    prometheusQuery = prometheusQuery + pair + ","
  prometheusQuery = prometheusQuery[0:len(prometheusQuery) - 1]
  prometheusQuery = metricName + "{" + prometheusQuery + "}"
  return prometheusQuery

def getMetrixNames(url):
  endpoint = '{0}/api/v1/label/__name__/values'.format(url)
  return makeRequest(endpoint, "It wasn't possible to get the metrics names.")

def getMetricTimeSeries(url, metricName, start, end):
  endpoint = '{0}/api/v1/series'.format(url)
  requestParams={'match[]': metricName, 'start': start, 'end': end }

  return makeRequest(endpoint, "It wasn't possible to get the time series set.", params=requestParams)

def createDir(destinationDirPath):
  try:
    shutil.rmtree(destinationDirPath)
  except Exception as e:
    pass
  try:
    os.mkdir(destinationDirPath)
  except Exception as e:
    raise e

def convertToHourFormat(offsetParam):
  hourFormat = '+' if (offsetParam >= 0) else '-'
  offset = abs(int(offsetParam))
  hourFormat = hourFormat + str(offset).zfill(2) + ':00'
  return hourFormat

def getFormatInSeconds(timeFormat):
  if timeFormat == 'h':
    return 3600
  if timeFormat == 'm':
    return 60
  return 1
