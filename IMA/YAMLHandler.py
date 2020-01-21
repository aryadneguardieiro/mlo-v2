import yaml
import Constants
from SliceConfig import slicesConfig
from collections import OrderedDict

def strRepresenter(dumper, data):
  return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"' if '[' in data else None)

def dict_representer(dumper, data):
    return dumper.represent_dict(data.items())

def setupYaml():
  yaml.add_representer(str, strRepresenter)
  yaml.add_representer(OrderedDict, dict_representer)


def doConfigMapYml(sliceId, metricsInfo, path):
  setupYaml()
  targetsAsString = str(slicesConfig[sliceId - 1]['targets'])
  metricsInfo = sorted(metricsInfo, key = lambda d : d['job'])
  configMap = OrderedDict()
  configMap['apiVersion'] = Constants.API_VERSION
  configMap['kind'] = 'ConfigMap'
  configMap['metadata'] = {'name':slicesConfig[sliceId - 1]['metadataName'], 'labels': {'name':slicesConfig[sliceId - 1]['metadataName']}, 'namespace': slicesConfig[sliceId - 1]['promNamespace']}

  data = OrderedDict()
  data['prometheus.yml'] = {"global" : {"scrape_interval" : slicesConfig[sliceId - 1]['scrapeInterval'], \
    "evaluation_interval": slicesConfig[sliceId - 1]['evaluationInterval']}, \
  'remote_write': [{"url" : slicesConfig[sliceId - 1]['urlToWrite']}]}

  currentJob = ''
  sourceLabels = ''

  rgx = set()
  jobConf = OrderedDict()

  scrapeConfigs = []

  for metricInfo in metricsInfo:
    if metricInfo['job'] != currentJob:
      if sourceLabels != '':
        jobConf = buildJobConf(currentJob, rgx, 'keep', sourceLabels, sliceId, targetsAsString)
        scrapeConfigs.append(jobConf)

      currentJob = metricInfo['job']
      sourceLabels = '[__name__]'
      rgx.add(metricInfo['__name__'])
    else:
      rgx.add(metricInfo['__name__'])

  if sourceLabels != '':
    jobConf = buildJobConf(currentJob, rgx, 'keep', sourceLabels, sliceId, targetsAsString)
    scrapeConfigs.append(jobConf)
  data['prometheus.yml']['scrape_configs'] = scrapeConfigs
  configMap['data']  = data
  configMapYAML = yaml.dump(configMap, default_flow_style=False, sort_keys=False, width=1000)
  configMapYAML = configMapYAML.replace("prometheus.yml:", "prometheus.yml: |-")
  
  configMapYAML = configMapYAML.replace('"', '')

  with open(path + "/config-map.yaml", "w") as configMapFile:
    configMapFile.write(configMapYAML)

def buildJobConf(currentJob, rgx, action, sourceLabels, sliceId, targetsAsString):
  first = True
  regx = ''
  for r in rgx:
    if not first:
      regx = regx + '|'
    regx = regx + r
    first = False
    
  jobConf = OrderedDict()
  jobConf['job_name'] = currentJob
  metricRelabelConfigs = OrderedDict()
  metricRelabelConfigs['source_labels'] = sourceLabels
  metricRelabelConfigs['regex'] = regx
  metricRelabelConfigs['action'] = action
  jobConf['metric_relabel_configs'] = [metricRelabelConfigs]
  jobConf['static_configs'] = [{'targets': targetsAsString }]
  return jobConf

"""

if __name__ == "__main__":
  doConfigMapYml(1, [{'beta_kubernetes_io_os': 'linux', '__name__': 'xhue', 'dojot': 'sim', 'instance': 'worker-k8s-1', \
    'beta_kubernetes_io_arch': 'amd64', 'job': 'kubernetes-nodes', 'quantile': '0', 'kubernetes_io_hostname': 'worker-k8s-1'}, \
    {'__name__': 'go_memstats_gc_cpu_fraction', 'job': 'node', 'instance': '192.168.0.107:9100'}, \
    {'beta_kubernetes_io_os': 'linux', '__name__': 'process_resident_memory_bytes', 'instance': 'cloud17', \
      'beta_kubernetes_io_arch': 'arm', 'job': 'kubernetes-nodes', 'kubernetes_io_hostname': 'cloud17'}, \
    {'beta_kubernetes_io_os': 'linux', '__name__': 'go_gc_duration_seconds', 'dojot': 'sim', 'instance': 'worker-k8s-1', \
      'beta_kubernetes_io_arch': 'amd64', 'job': 'kubernetes-nodes', 'quantile': '0.25', 'kubernetes_io_hostname': 'worker-k8s-1'}])
apiVersion: v1
data:
  prometheus.yml: |-
    global:
      scrape_interval: 1s
      evaluation_interval: 15s

    remote_write:
      - url: "http://192.168.0.111:8080/receive"

    scrape_configs:
      - job_name: node
        static_configs:
        - targetsAsString: ['192.168.0.107', ] #se adicionar mais ip's, separar por virgula dentro dos colchetes
kind: ConfigMap
metadata:
  name: prometheus-2-server-conf
  labels:
    name: prometheus-2-server-conf
  namespace: monitoring2
  """
