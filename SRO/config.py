import logging

#IMA_IP='200.19.151.94'
IMA_IP='192.168.0.129'
IMA_METRICS_ENDPOINT = 'http://{}:5000/ymetrics/'.format(IMA_IP)
IMA_ELASTICITY_ENDPOINT = 'http://{}:5000/elasticity/slice/slice_id/flavor/flavor_id'.format(IMA_IP)
SRO_SERVER_HOST = '192.168.0.121'
#SRO_SERVER_HOST = 'localhost'
SERVER_RECEIVE_AGGREATED_METRICS_URL = 'http://{}:13131/slice/slice_id/flavor/flavor_id/profilling_metrics'.format(SRO_SERVER_HOST)
KAFKA_ENDPOINT='192.168.0.123:9092'

formatter = logging.Formatter('\n[[  %(asctime)s - %(name)s - %(message)s  ]]')
#formatter = logging.Formatter('%(message)s')
ch = logging.StreamHandler()
ch.setFormatter(formatter)
ch.setLevel(logging.INFO)
logger = logging.getLogger('SRO Application')
logger.setLevel(logging.INFO)
logger.addHandler(ch)

