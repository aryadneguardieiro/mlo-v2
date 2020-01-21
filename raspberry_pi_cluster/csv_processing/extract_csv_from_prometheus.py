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

# code based on:
# https://www.robustperception.io/prometheus-query-results-as-csv and
# https://medium.com/@aneeshputtur/export-data-from-prometheus-to-csv-b19689d780aa

def GetMetrixNames(url):
    response = requests.get('{0}/api/v1/label/__name__/values'.format(url))
    names = response.json()['data']
    #Return metrix names
    return names

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

def get_hour_in_minutes(begin_hour_test):
    hour = int(begin_hour_test.split(':')[0])
    return ((24 - hour) * 60)

def get_minute(begin_hour_test):
    return (int(begin_hour_test.split(':')[1]))

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

"""
Prometheus hourly data as csv.
"""

if len(sys.argv) != 7:
    print('Usage: {0} http://localhost:30000 duration(1m,2h,...) dir_path begin_test_day (dd/mm/aa) begin_test_hour (hh:mm:ss) step'.format(sys.argv[0]))
    sys.exit(1)

metrixNames=GetMetrixNames(sys.argv[1])
interval=sys.argv[2]
interval_int = int(sys.argv[2][:-1]) * getFormatInSeconds(sys.argv[2][-1:])
path=sys.argv[3]
begin_hour_test=sys.argv[5]
step=int(sys.argv[6])
create_dir(path)
s = requests.Session()
offset_til_midnight = get_hour_in_minutes(begin_hour_test) - get_minute(begin_hour_test)
begin_test_date = datetime.strptime(sys.argv[4]+ ' ' + sys.argv[5], "%d/%m/%y %H:%M:%S")
current = 0
total = len(metrixNames)

if interval_int % step != 0:
    print('Step nao divide o intervalo.')
    exit()
metrics_to_get=["go_gc_duration_seconds", "go_goroutines", "go_info", "go_memstats_alloc_bytes", "go_memstats_alloc_bytes_total", "go_memstats_buck_hash_sys_bytes", "go_memstats_frees_total", "go_memstats_gc_cpu_fraction", "go_memstats_gc_sys_bytes", "go_memstats_heap_alloc_bytes", "go_memstats_heap_idle_bytes", "go_memstats_heap_inuse_bytes", "go_memstats_heap_objects", "go_memstats_heap_released_bytes", "go_memstats_heap_sys_bytes", "go_memstats_last_gc_time_seconds", "go_memstats_lookups_total", "go_memstats_mallocs_total", "go_memstats_mcache_inuse_bytes", "go_memstats_mcache_sys_bytes", "go_memstats_mspan_inuse_bytes", "go_memstats_mspan_sys_bytes", "go_memstats_next_gc_bytes", "go_memstats_other_sys_bytes", "go_memstats_stack_inuse_bytes", "go_memstats_stack_sys_bytes", "go_memstats_sys_bytes", "go_threads", "node_arp_entries", "node_boot_time_seconds", "node_context_switches_total", "node_cpu_guest_seconds_total", "node_cpu_seconds_total", "node_disk_io_now", "node_disk_io_time_seconds_total", "node_disk_io_time_weighted_seconds_total", "node_disk_read_bytes_total", "node_disk_read_time_seconds_total", "node_disk_reads_completed_total", "node_disk_reads_merged_total", "node_disk_write_time_seconds_total", "node_disk_writes_completed_total", "node_disk_writes_merged_total", "node_disk_written_bytes_total", "node_entropy_available_bits", "node_exporter_build_info", "node_filefd_allocated", "node_filefd_maximum", "node_filesystem_avail_bytes", "node_filesystem_device_error", "node_filesystem_files", "node_filesystem_files_free", "node_filesystem_free_bytes", "node_filesystem_readonly", "node_filesystem_size_bytes", "node_forks_total", "node_intr_total", "node_load1", "node_load15", "node_load5", "node_memory_Active_anon_bytes", "node_memory_Active_bytes", "node_memory_Active_file_bytes", "node_memory_AnonHugePages_bytes", "node_memory_AnonPages_bytes", "node_memory_Bounce_bytes", "node_memory_Buffers_bytes", "node_memory_Cached_bytes", "node_memory_CmaFree_bytes", "node_memory_CmaTotal_bytes", "node_memory_CommitLimit_bytes", "node_memory_Committed_AS_bytes", "node_memory_DirectMap1G_bytes", "node_memory_DirectMap2M_bytes", "node_memory_DirectMap4k_bytes", "node_memory_Dirty_bytes", "node_memory_HardwareCorrupted_bytes", "node_memory_HugePages_Free", "node_memory_HugePages_Rsvd", "node_memory_HugePages_Surp", "node_memory_HugePages_Total", "node_memory_Hugepagesize_bytes", "node_memory_Inactive_anon_bytes", "node_memory_Inactive_bytes", "node_memory_Inactive_file_bytes", "node_memory_KernelStack_bytes", "node_memory_Mapped_bytes", "node_memory_MemAvailable_bytes", "node_memory_MemFree_bytes", "node_memory_MemTotal_bytes", "node_memory_Mlocked_bytes", "node_memory_NFS_Unstable_bytes", "node_memory_PageTables_bytes", "node_memory_SReclaimable_bytes", "node_memory_SUnreclaim_bytes", "node_memory_Shmem_bytes", "node_memory_Slab_bytes", "node_memory_SwapCached_bytes", "node_memory_SwapFree_bytes", "node_memory_SwapTotal_bytes", "node_memory_Unevictable_bytes", "node_memory_VmallocChunk_bytes", "node_memory_VmallocTotal_bytes", "node_memory_VmallocUsed_bytes", "node_memory_WritebackTmp_bytes", "node_memory_Writeback_bytes", "node_netstat_Icmp6_InErrors", "node_netstat_Icmp6_InMsgs", "node_netstat_Icmp6_OutMsgs", "node_netstat_Icmp_InErrors", "node_netstat_Icmp_InMsgs", "node_netstat_Icmp_OutMsgs", "node_netstat_Ip6_InOctets", "node_netstat_Ip6_OutOctets", "node_netstat_IpExt_InOctets", "node_netstat_IpExt_OutOctets", "node_netstat_Ip_Forwarding", "node_netstat_TcpExt_ListenDrops", "node_netstat_TcpExt_ListenOverflows", "node_netstat_TcpExt_SyncookiesFailed", "node_netstat_TcpExt_SyncookiesRecv", "node_netstat_TcpExt_SyncookiesSent", "node_netstat_Tcp_ActiveOpens", "node_netstat_Tcp_CurrEstab", "node_netstat_Tcp_InErrs", "node_netstat_Tcp_PassiveOpens", "node_netstat_Tcp_RetransSegs", "node_netstat_Udp6_InDatagrams", "node_netstat_Udp6_InErrors", "node_netstat_Udp6_NoPorts", "node_netstat_Udp6_OutDatagrams", "node_netstat_UdpLite6_InErrors", "node_netstat_UdpLite_InErrors", "node_netstat_Udp_InDatagrams", "node_netstat_Udp_InErrors", "node_netstat_Udp_NoPorts", "node_netstat_Udp_OutDatagrams", "node_network_address_assign_type", "node_network_carrier", "node_network_carrier_changes_total", "node_network_device_id", "node_network_dormant", "node_network_flags", "node_network_iface_id", "node_network_iface_link", "node_network_iface_link_mode", "node_network_mtu_bytes", "node_network_name_assign_type", "node_network_net_dev_group", "node_network_protocol_type", "node_network_receive_bytes_total", "node_network_receive_compressed_total", "node_network_receive_drop_total", "node_network_receive_errs_total", "node_network_receive_fifo_total", "node_network_receive_frame_total", "node_network_receive_multicast_total", "node_network_receive_packets_total", "node_network_speed_bytes", "node_network_transmit_bytes_total", "node_network_transmit_carrier_total", "node_network_transmit_colls_total", "node_network_transmit_compressed_total", "node_network_transmit_drop_total", "node_network_transmit_errs_total", "node_network_transmit_fifo_total", "node_network_transmit_packets_total", "node_network_transmit_queue_length", "node_network_up", "node_procs_blocked", "node_procs_running", "node_scrape_collector_duration_seconds", "node_scrape_collector_success", "node_sockstat_FRAG_inuse", "node_sockstat_FRAG_memory", "node_sockstat_RAW_inuse", "node_sockstat_TCP_alloc", "node_sockstat_TCP_inuse", "node_sockstat_TCP_mem", "node_sockstat_TCP_mem_bytes", "node_sockstat_TCP_orphan", "node_sockstat_TCP_tw", "node_sockstat_UDPLITE_inuse", "node_sockstat_UDP_inuse", "node_sockstat_UDP_mem", "node_sockstat_UDP_mem_bytes", "node_sockstat_sockets_used", "node_textfile_scrape_error", "node_time_seconds", "node_timex_estimated_error_seconds", "node_timex_frequency_adjustment_ratio", "node_timex_loop_time_constant", "node_timex_maxerror_seconds", "node_timex_offset_seconds", "node_timex_pps_calibration_total", "node_timex_pps_error_total", "node_timex_pps_frequency_hertz", "node_timex_pps_jitter_seconds", "node_timex_pps_jitter_total", "node_timex_pps_shift_seconds", "node_timex_pps_stability_exceeded_total", "node_timex_pps_stability_hertz", "node_timex_status", "node_timex_sync_status", "node_timex_tai_offset_seconds", "node_timex_tick_seconds", "node_uname_info", "node_vmstat_pgfault", "node_vmstat_pgmajfault", "node_vmstat_pgpgin", "node_vmstat_pgpgout", "node_vmstat_pswpin", "node_vmstat_pswpout", "process_cpu_seconds_total", "process_max_fds", "process_open_fds", "process_resident_memory_bytes", "process_start_time_seconds", "process_virtual_memory_bytes", "process_virtual_memory_max_bytes", "promhttp_metric_handler_requests_in_flight", "promhttp_metric_handler_requests_total"]

for metrixName in metrixNames:
    if metrixName not in metrics_to_get:
        continue

    print("Starting: " + metrixName)
    with open(path + '/' + metrixName + '.csv', 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
        try:
            offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
            offset = offset / (-3600)
            offsetFormatted = '.000' + convertToHourFormat(offset)

            labelnames = set()
            time_series = {}
            start = begin_test_date
            end_test_date = start + timedelta(seconds=interval_int)
            step_in_seconds = (interval_int / step)
            shift=timedelta(seconds=step_in_seconds)
            for current_step in range(1, step + 1):

                end = start + shift
                if end > end_test_date:
                    end = end_test_date
                response = s.get('{0}/api/v1/query_range'.format(sys.argv[1]), params={'query': metrixName, 'start': start.isoformat() + offsetFormatted, 'end': end.isoformat() + offsetFormatted, 'step': '1s'}, timeout=120)
                print("End request for: " + metrixName)
                results = response.json()['data']['result']
                if current_step == 1:
                    for result in results:
                        labelnames.update(result['metric'].keys())

                    # Canonicalize
                    labelnames.discard('__name__')
                    labelnames = sorted(labelnames)

                    # Write the samples.
                    writer.writerow(['name'] + labelnames + ['timestamp', 'value'])
                for result in results:
                    for value in result['values']:
                        l = [result['metric'].get('__name__', '')]
                        tag = result['metric'].get('__name__', '')

                        for label in labelnames:
                            l.append(result['metric'].get(label, ''))
                            tag = tag +'_'+ result['metric'].get(label, '')
                        l.append(value[0])
                        l.append(value[1])
                        writer.writerow(l)

                        if tag in time_series:
                            if time_series[tag]['x'][-1] != value[0] and time_series[tag]['y'][-1] != value[1]:
                                time_series[tag]['x'] = time_series[tag]['x'] + [value[0]]
                                time_series[tag]['y'] = time_series[tag]['y'] + [value[1]]
                        else:
                            time_series[tag] = {'x': [value[0]], 'y': [value[1]]}
                start = end + timedelta(seconds=1)
                print("Step: " + str(current_step) + " concluido para a metrica: " + metrixName, end='\r')
            current = current + 1
            percentage = current/total * 100
            print("\n" + str(math.ceil(percentage)) + "% arquivos gerados (" +str(current) + "/" + str(total) + ")")
        except Exception as e:
            print("\nNao foi possivel gerar "+ metrixName)
            print("Exception: ")
            print(e)
            percentage = current/total * 100
            print(str(math.ceil(percentage)) + "% arquivos gerados (" +str(current) + "/" + str(total) + ")")
