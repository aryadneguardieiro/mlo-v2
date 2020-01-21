import flask
from flask import request
from ReceiveConfigMapService import runPrometheus
import pdb

app = flask.Flask(__name__)

@app.route("/configmap", methods = ['POST'])
def postConfigMap():
  #pdb.set_trace()
  configMap = request.files['configMap']
  print("Config map received from IMA")
  configMap.save('/home/cloud/raspberry_pi_cluster/prometheus-2-files/config-map.yaml', buffer_size = 16384)
  configMap.close()
  print("Running prometheus to collect selected metrics")
  runPrometheus()
  print("Ok, prometheus running")
  return "Ok!", 200

if __name__ == "__main__":
  app.run(host='192.168.0.30', port=5000)
