from flask import Flask
from flask import request
from flask import jsonify
from IMAService import IMAService
import Constants
import asyncio
import pdb
import time
import sys

app = Flask(__name__)

@app.route("/ymetrics/<int:sliceId>", methods = ['POST'])
def postYMetrics(sliceId):
  try:
    if (not 'callbackURL' in request.form) or (not 'K' in request.form) or (not 'YField' in request.form) or (not 'sliceFlavor' in request.form) or (not 'YFile' in request.files and 'currentTimestamp' in request.form):
      return "Missing paramenters: callbackURL OR K OR YField OR sliceFlavor OR (YFile or currentTimestamp)", 400

    callbackURL = request.form['callbackURL']
    K = request.form['K']
    sliceFlavor = request.form['sliceFlavor']
    YField = None
    if 'YField' in request.form:
      YField = request.form['YField']
    executePrometheus = True
    path = Constants.SLICE_FILES_DIR + Constants.SLICE_DIR_NAME + str(sliceId) + Constants.FLAVOR_DIR_NAME + sliceFlavor
    if 'currentTimestamp' in request.form:
      executePrometheus = False
      currentTimestamp = request.form['currentTimestamp']
    else:
      IMAService.createDir(path)
      currentTimestamp = int(time.time())
      YFile = request.files['YFile']
      YFile.save(path + "/YFile{0}.csv".format(currentTimestamp), buffer_size = 16384)
      YFile.close()

    IMAService(sliceId, callbackURL, K, YField, currentTimestamp, sliceFlavor, executePrometheus, path).start()

    message={"text" : "Ok, IMAService has started.", "currentTimestamp" : currentTimestamp}
    return jsonify(result=message), 201
  except Exception as e:
    return 'Something went wrong.\n ' + str(e) + '\n', 400

@app.route("/elasticity/slice/<int:sliceId>/flavor/<string:sliceFlavor>", methods = ['POST'])
def postElasticity(sliceId, sliceFlavor):
  path = Constants.SLICE_FILES_DIR + Constants.SLICE_DIR_NAME + str(sliceId) + Constants.FLAVOR_DIR_NAME + sliceFlavor
  if IMAService.sendNewConfigMap(sliceId, sliceFlavor, path):
    return "Ok", 200
  else:
    return "Error", 400

if __name__ == "__main__":
  if len(sys.argv) == 1:
    app.run(host='192.168.0.129', port=5000)
  else:
    if len(sys.argv) != 7:
      print("Wrong number of arguments. Please review!\nNeed sliceId, K, YField, currentTimestamp, sliceFlavor and executePrometheusFlag, in this order.")
      exit(1)

    sliceId = int(sys.argv[1])
    K = int(sys.argv[2])
    YField = sys.argv[3]
    currentTimestamp = int(sys.argv[4])
    sliceFlavor = sys.argv[5]
    executePrometheus = sys.argv[6]
    callbackURL = 'http://teste.com'
    path = Constants.SLICE_FILES_DIR + Constants.SLICE_DIR_NAME + str(sliceId) + Constants.FLAVOR_DIR_NAME + sliceFlavor
    IMAService(sliceId, callbackURL, K, YField, currentTimestamp, sliceFlavor, (True if executePrometheus == 's' else False) , path).start()
