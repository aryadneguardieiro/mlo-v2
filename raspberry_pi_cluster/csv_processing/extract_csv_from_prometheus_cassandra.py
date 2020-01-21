from __future__ import print_function
import csv
import requests
import sys
import os # mkdir
import shutil # rmtree
import pdb
import math
import datetime
import time
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from functools import reduce
import hashlib

# code based on:
# https://www.robustperception.io/prometheus-query-results-as-csv and
# https://medium.com/@aneeshputtur/export-data-from-prometheus-to-csv-b19689d780aa

STEP_PROMETHEUS = '1s'

def main():
  if len(sys.argv) != 7:
    print('Usage: {0} http://localhost:30000 duration(1m,2h,...) destination_dir_path begin_test_day (dd/mm/aa) begin_test_hour (hh:mm:ss) step'.format(sys.argv[0]))
    sys.exit(1)

  prometheus_url = sys.argv[1]
  duration=int(sys.argv[2][:-1])
  time_unity = sys.argv[2][-1]
  destination_dir_path=sys.argv[3]
  begin_test_day = sys.argv[4]
  begin_test_hour=sys.argv[5]
  step=int(sys.argv[6])

  if duration % step != 0:
    print('Step nao divide o intervalo.')
    exit()
  
  create_dir(destination_dir_path)
  data_folder = Path(destination_dir_path)
  start = datetime.strptime(begin_test_day + ' ' + begin_test_hour, "%d/%m/%y %H:%M:%S")
  duration_in_sec = duration * getFormatInSeconds(time_unity)
  start_formated, end_formated = format_start_end_time(start, timedelta(seconds=duration_in_sec))

  map_file_name = 'time_series_map.csv'
  map_file_name = data_folder / map_file_name
  
  metric_names=get_metrix_names(prometheus_url)
  metric_count = 0
  metrics_to_get=["go_gc_duration_seconds", "go_goroutines", "go_info", "go_memstats_alloc_bytes", "go_memstats_alloc_bytes_total", "go_memstats_buck_hash_sys_bytes", "go_memstats_frees_total", "go_memstats_gc_cpu_fraction", "go_memstats_gc_sys_bytes", "go_memstats_heap_alloc_bytes", "go_memstats_heap_idle_bytes", "go_memstats_heap_inuse_bytes", "go_memstats_heap_objects", "go_memstats_heap_released_bytes", "go_memstats_heap_sys_bytes", "go_memstats_last_gc_time_seconds", "go_memstats_lookups_total", "go_memstats_mallocs_total", "go_memstats_mcache_inuse_bytes", "go_memstats_mcache_sys_bytes", "go_memstats_mspan_inuse_bytes", "go_memstats_mspan_sys_bytes", "go_memstats_next_gc_bytes", "go_memstats_other_sys_bytes", "go_memstats_stack_inuse_bytes", "go_memstats_stack_sys_bytes", "go_memstats_sys_bytes", "go_threads", "node_arp_entries", "node_boot_time_seconds", "node_context_switches_total", "node_cpu_guest_seconds_total", "node_cpu_seconds_total", "node_disk_io_now", "node_disk_io_time_seconds_total", "node_disk_io_time_weighted_seconds_total", "node_disk_read_bytes_total", "node_disk_read_time_seconds_total", "node_disk_reads_completed_total", "node_disk_reads_merged_total", "node_disk_write_time_seconds_total", "node_disk_writes_completed_total", "node_disk_writes_merged_total", "node_disk_written_bytes_total", "node_entropy_available_bits", "node_exporter_build_info", "node_filefd_allocated", "node_filefd_maximum", "node_filesystem_avail_bytes", "node_filesystem_device_error", "node_filesystem_files", "node_filesystem_files_free", "node_filesystem_free_bytes", "node_filesystem_readonly", "node_filesystem_size_bytes", "node_forks_total", "node_intr_total", "node_load1", "node_load15", "node_load5", "node_memory_Active_anon_bytes", "node_memory_Active_bytes", "node_memory_Active_file_bytes", "node_memory_AnonHugePages_bytes", "node_memory_AnonPages_bytes", "node_memory_Bounce_bytes", "node_memory_Buffers_bytes", "node_memory_Cached_bytes", "node_memory_CmaFree_bytes", "node_memory_CmaTotal_bytes", "node_memory_CommitLimit_bytes", "node_memory_Committed_AS_bytes", "node_memory_DirectMap1G_bytes", "node_memory_DirectMap2M_bytes", "node_memory_DirectMap4k_bytes", "node_memory_Dirty_bytes", "node_memory_HardwareCorrupted_bytes", "node_memory_HugePages_Free", "node_memory_HugePages_Rsvd", "node_memory_HugePages_Surp", "node_memory_HugePages_Total", "node_memory_Hugepagesize_bytes", "node_memory_Inactive_anon_bytes", "node_memory_Inactive_bytes", "node_memory_Inactive_file_bytes", "node_memory_KernelStack_bytes", "node_memory_Mapped_bytes", "node_memory_MemAvailable_bytes", "node_memory_MemFree_bytes", "node_memory_MemTotal_bytes", "node_memory_Mlocked_bytes", "node_memory_NFS_Unstable_bytes", "node_memory_PageTables_bytes", "node_memory_SReclaimable_bytes", "node_memory_SUnreclaim_bytes", "node_memory_Shmem_bytes", "node_memory_Slab_bytes", "node_memory_SwapCached_bytes", "node_memory_SwapFree_bytes", "node_memory_SwapTotal_bytes", "node_memory_Unevictable_bytes", "node_memory_VmallocChunk_bytes", "node_memory_VmallocTotal_bytes", "node_memory_VmallocUsed_bytes", "node_memory_WritebackTmp_bytes", "node_memory_Writeback_bytes", "node_netstat_Icmp6_InErrors", "node_netstat_Icmp6_InMsgs", "node_netstat_Icmp6_OutMsgs", "node_netstat_Icmp_InErrors", "node_netstat_Icmp_InMsgs", "node_netstat_Icmp_OutMsgs", "node_netstat_Ip6_InOctets", "node_netstat_Ip6_OutOctets", "node_netstat_IpExt_InOctets", "node_netstat_IpExt_OutOctets", "node_netstat_Ip_Forwarding", "node_netstat_TcpExt_ListenDrops", "node_netstat_TcpExt_ListenOverflows", "node_netstat_TcpExt_SyncookiesFailed", "node_netstat_TcpExt_SyncookiesRecv", "node_netstat_TcpExt_SyncookiesSent", "node_netstat_Tcp_ActiveOpens", "node_netstat_Tcp_CurrEstab", "node_netstat_Tcp_InErrs", "node_netstat_Tcp_PassiveOpens", "node_netstat_Tcp_RetransSegs", "node_netstat_Udp6_InDatagrams", "node_netstat_Udp6_InErrors", "node_netstat_Udp6_NoPorts", "node_netstat_Udp6_OutDatagrams", "node_netstat_UdpLite6_InErrors", "node_netstat_UdpLite_InErrors", "node_netstat_Udp_InDatagrams", "node_netstat_Udp_InErrors", "node_netstat_Udp_NoPorts", "node_netstat_Udp_OutDatagrams", "node_network_address_assign_type", "node_network_carrier", "node_network_carrier_changes_total", "node_network_device_id", "node_network_dormant", "node_network_flags", "node_network_iface_id", "node_network_iface_link", "node_network_iface_link_mode", "node_network_mtu_bytes", "node_network_name_assign_type", "node_network_net_dev_group", "node_network_protocol_type", "node_network_receive_bytes_total", "node_network_receive_compressed_total", "node_network_receive_drop_total", "node_network_receive_errs_total", "node_network_receive_fifo_total", "node_network_receive_frame_total", "node_network_receive_multicast_total", "node_network_receive_packets_total", "node_network_speed_bytes", "node_network_transmit_bytes_total", "node_network_transmit_carrier_total", "node_network_transmit_colls_total", "node_network_transmit_compressed_total", "node_network_transmit_drop_total", "node_network_transmit_errs_total", "node_network_transmit_fifo_total", "node_network_transmit_packets_total", "node_network_transmit_queue_length", "node_network_up", "node_procs_blocked", "node_procs_running", "node_scrape_collector_duration_seconds", "node_scrape_collector_success", "node_sockstat_FRAG_inuse", "node_sockstat_FRAG_memory", "node_sockstat_RAW_inuse", "node_sockstat_TCP_alloc", "node_sockstat_TCP_inuse", "node_sockstat_TCP_mem", "node_sockstat_TCP_mem_bytes", "node_sockstat_TCP_orphan", "node_sockstat_TCP_tw", "node_sockstat_UDPLITE_inuse", "node_sockstat_UDP_inuse", "node_sockstat_UDP_mem", "node_sockstat_UDP_mem_bytes", "node_sockstat_sockets_used", "node_textfile_scrape_error", "node_time_seconds", "node_timex_estimated_error_seconds", "node_timex_frequency_adjustment_ratio", "node_timex_loop_time_constant", "node_timex_maxerror_seconds", "node_timex_offset_seconds", "node_timex_pps_calibration_total", "node_timex_pps_error_total", "node_timex_pps_frequency_hertz", "node_timex_pps_jitter_seconds", "node_timex_pps_jitter_total", "node_timex_pps_shift_seconds", "node_timex_pps_stability_exceeded_total", "node_timex_pps_stability_hertz", "node_timex_status", "node_timex_sync_status", "node_timex_tai_offset_seconds", "node_timex_tick_seconds", "node_uname_info", "node_vmstat_pgfault", "node_vmstat_pgmajfault", "node_vmstat_pgpgin", "node_vmstat_pgpgout", "node_vmstat_pswpin", "node_vmstat_pswpout", "process_cpu_seconds_total", "process_max_fds", "process_open_fds", "process_resident_memory_bytes", "process_start_time_seconds", "process_virtual_memory_bytes", "process_virtual_memory_max_bytes", "promhttp_metric_handler_requests_in_flight", "promhttp_metric_handler_requests_total"]
  
  with open(str(map_file_name), 'w') as time_series_map:
    writer_file_map = csv.writer(time_series_map, delimiter=',', quoting=csv.QUOTE_MINIMAL)
    writer_file_map.writerow(['hash', 'metric_name', 'metric_info'])
    for metric_name in metric_names:
      if metric_name not in metrics_to_get:
        continue
      try:
        print("Metrics already evaluated: {0} of {1}".format(metric_count, len(metric_names)))

        time_series = get_metric_time_series(prometheus_url, metric_name, start_formated, end_formated)


        for _, time_serie in enumerate(time_series):

          results = request_time_serie_values(prometheus_url, time_serie, start, duration_in_sec, step)

          if 'result' in results and len(results['result']) > 0:
            result = results['result'][0]
          else:
            raise Exception("result with unknown format: {0}".format(str(results)))

          if 'metric' in result and 'values' in result and len(result['values']) > 0 : 
            first_value=result['values'][0][1]
            print_values=False

            for value in result['values']:
              if value[1] != first_value: 
                  print_values=True
                  break

            if print_values:
              metric_info = str(result['metric'])
              hash_object = hashlib.sha1(metric_info.encode())
              time_serie_hash_id = hash_object.hexdigest()

              writer_file_map.writerow([time_serie_hash_id, metric_name, metric_info])

              file_name = time_serie_hash_id + '.csv'
              file_name = data_folder / file_name

              with open(str(file_name), 'w') as csvfile:
                writer = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(['timestamp', 'value'])

                for value in result['values']:
                  writer.writerow(value)
        metric_count = metric_count + 1 
      except Exception as e:
        print("\nNao foi possivel gerar "+ metric_name)
        print("Exception: ")
        print(e)


def format_start_end_time(start, shift_time):
  offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
  offset = offset / (-3600)
  offsetFormatted = '.000' + convertToHourFormat(offset)
  end_test_date = start + shift_time
  start_formated = start.isoformat() + offsetFormatted
  end_formated = end_test_date.isoformat() + offsetFormatted
  return start_formated, end_formated

def make_request(url, error_message, params={}):
  response = requests.get(url, params=params, timeout=120)

  data = response.json()['data']

  if not response or response.status_code != requests.codes.ok or not data:
    raise Exception(error_message + "\nURL: " + url + "\nParams: " + params + "\nReponse: " + response)

  return data

def request_time_serie_values(url, time_serie, start, duration_in_sec, step):
  endpoint = '{0}/api/v1/query_range'.format(url)
  metric_name = time_serie.pop('__name__')
  prometheus_query = create_prom_query(metric_name, time_serie)
  start_part = start
  end = start + timedelta(seconds=duration_in_sec)
  stop = False
  shift_time = timedelta(seconds=int(duration_in_sec / step))
  one_second = timedelta(seconds=1)
  data = None
  
  while not stop:
    end_part = start_part + shift_time
    if end_part >= end:
      end_part = end
      stop = True
    start_part_formated, end_part_formated = format_start_end_time(start_part, shift_time)
    params = {'query': prometheus_query, 'start': start_part_formated, 'end': end_part_formated, 'step' : STEP_PROMETHEUS}
    step_data = make_request(endpoint, "It wasn't possible to retrive time serie values", params)
    if not data:
      data = step_data
    else:
      pdb.set_trace()
      data['result'][0]['values'] = data['result'][0]['values'] + step_data['result'][0]['values']
    start_part = end_part + one_second
  return data

def create_prom_query (metric_name, time_serie):
  prometheus_query = ""
  for label, value in time_serie.items():
    pair = label.replace("'","") + "=" + '"' + value + '"'
    prometheus_query = prometheus_query + pair + ","
  prometheus_query = prometheus_query[0:len(prometheus_query) - 1]
  prometheus_query = metric_name+ "{" + prometheus_query + "}"
  return prometheus_query

def get_metrix_names(url):
  endpoint = '{0}/api/v1/label/__name__/values'.format(url)

  return make_request(endpoint, "It wasn't possible to get the metrics names.")

def get_metric_time_series(url, metric_name, start, end):
  endpoint = '{0}/api/v1/series'.format(url)
  request_params={'match[]': metric_name, 'start': start, 'end': end }

  return make_request(endpoint, "It wasn't possible to get the time series set.", params=request_params)

def create_dir(destination_dir_path):
  try:
    shutil.rmtree(destination_dir_path)
  except Exception as e:
    print("Directory not deleted")
  try:
    os.mkdir(destination_dir_path)
  except Exception as e:
    print("Error at the creation of directory")
    sys.exit(1)

def get_hour_in_minutes(begin_test_hour):
  hour = int(begin_test_hour.split(':')[0])
  return ((24 - hour) * 60)

def get_minute(begin_test_hour):
  return (int(begin_test_hour.split(':')[1]))

def convertToHourFormat(offsetParam):
  hourFormat = '+' if (offsetParam > 0) else '-'
  offset = abs(int(offsetParam))
  hourFormat = hourFormat + str(offset).zfill(2) + ':00'
  return hourFormat

def getFormatInSeconds(timeFormat):
  if timeFormat == 'h':
    return 3600
  if timeFormat == 'm':
    return 60
  return 1

if __name__ == "__main__":
  main()
