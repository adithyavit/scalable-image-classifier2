import json
import os
import subprocess
import signal

from sys import argv, exit

import boto
import boto3
import boto.s3
import boto.sqs

from boto.s3.key import Key
from boto.sqs.message import Message

# app = Flask(__name__)

# @app.route('/')
def index():

  awsRegion = "us-east-1"
  bucketName = "imagebucket-adithya"
  sqsQueueName =  "course-queue"

  # sqs = boto3.resource('sqs')
  # queue = sqs.get_queue_by_name(QueueName=sqs_queue_name)

  s3 = boto.s3.connect_to_region(awsRegion)
  sqs = boto.sqs.connect_to_region(awsRegion)
  sqsQueue =  sqs.lookup(sqsQueueName)
  print("Getting messages from SQS queue...")
  messages = sqsQueue.get_messages(wait_time_seconds=20)
  workDir = "classifier"
  if messages:
      for m in messages:
          print(m)
          job = json.loads(m.get_body())
          print("Message received")
          action = job[0]
          if action == 'process':
              s3BucketName = job[1]
              s3InputPrefix = job[2]
              s3OutputPrefix = job[3]
              fileName = job[4]
              print(job[1])
              print(job[2])
              print(job[3])
              status = process(s3, s3BucketName, s3InputPrefix, s3OutputPrefix, fileName, workDir)
              if (status):
                  print("Message processed correctly ...")
                  m.delete()
  else:
      print("No Messages")
  return "hi"

def process(s3, s3BucketName, s3InputPrefix, s3OutputPrefix, fileName, workDir):
    print(s3BucketName+s3InputPrefix)
    s3BucketInput = s3.get_bucket(s3BucketName+"-"+s3InputPrefix)
    s3BucketOutput = s3.get_bucket(s3BucketName+"-"+s3OutputPrefix)
    localInputPath = os.path.join(workDir, fileName)
    localOutputPath =  os.path.join(workDir, fileName[:-4]+'.txt')
    remoteInputPath = fileName
    remoteOutputPath =  fileName[:-4]+'.txt'
    if not os.path.isdir(workDir):
        os.system('sudo mkdir work && sudo chmod 777 work')
    print("Downloading %s from s3://%s/%s ..." % (localInputPath, s3BucketName, remoteInputPath))
    #print(remoteInputPath)
    key = s3BucketInput.get_key(remoteInputPath)
    print("here1")
    s3 = boto3.client('s3')
    print("here2")
    print("s3BucketInput")
    print(s3BucketInput)
    print("remoteInputPath")
    print(remoteInputPath)
    print("localInputPath")
    print(localInputPath)
    s3.download_file(s3BucketName+"-"+"inputfolder", remoteInputPath, localInputPath)
    print("here3")
    key.get_contents_to_filename(workDir+"/"+fileName)
    #subprocess.call(['./darknet','detector','demo','cfg/coco.data','cfg/yolov3-tiny.cfg','yolov3-tiny.weights', localInputPath,'outpt.txt'])
    print("hi1")
    #ans = os.system('python3 classifier/image_classification.py '+localInputPath)
    os.system('python3 classifier/image_classification.py '+localInputPath+' > '+localOutputPath)
    print("hi2")
    #print(ans)
    print("hi2")
    print(localOutputPath)

    print("Uploading %s to s3://%s/%s ..." % (localOutputPath, s3BucketInput, remoteOutputPath))
    key = Key(s3BucketOutput)
    key.key = remoteOutputPath
    key.set_contents_from_filename(localOutputPath)
    return True


def main():
    getJobs(workDir, sqsQueueName, awsRegion)

if __name__ == '__main__':

    index()
