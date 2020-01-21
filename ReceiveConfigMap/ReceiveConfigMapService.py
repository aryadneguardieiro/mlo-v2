import subprocess

def runPrometheus():
  try:
    subprocess.call(['./up_prometheus', 'stop'])
  except:
    raise Exception("Error Unknown")
