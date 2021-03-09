#!usr/bin/python
import boto3
import json
import paramiko
import threading
import time
import os
import boto
import sys
from time import sleep
import subprocess
import signal
from sys import argv, exit

import boto.s3
import boto.sqs
from boto.s3.key import Key
from boto.sqs.message import Message

# AWS_KEY_ID =  os.environ.get("AWS_KEY_ID") 
# AWS_SECRET =  os.environ.get("AWS_SECRET")
instanceIds=[]
instanceCount=0
myInstanceId=''
awsRegion = 'us-east-1'
MASTER_ID = 'i-0ed4ef8e0b534a642'
# workDir = 'classification'
workDir = ''

def getLengthOfQ(client, sqsQueueUrl):
    response = client.get_queue_attributes(QueueUrl=sqsQueueUrl,AttributeNames=['ApproximateNumberOfMessages',])
    response = int(response['Attributes']['ApproximateNumberOfMessages'])
    return response


def getNumberOfInstances(ec2):
    runningCount = 0
    stoppedCount = 0
    for instance in ec2.instances.all():
        if(instance.state['Name']=='running' and instance.id != MASTER_ID):
            runningCount+=1
        elif(instance.state['Name']=='stopped' and instance.id != MASTER_ID):
            stoppedCount+=1

    return runningCount, stoppedCount

def getRunningIds(ec2):
    ids = []
    for instance in ec2.instances.all():
        if(instance.state['Name']=='running' and instance.id != MASTER_ID):
            ids.append(instance.id)
    return ids
def getStoppedIds(ec2):
    ids = []
    for instance in ec2.instances.all():
        if(instance.state['Name']=='stopped' and instance.id != MASTER_ID):
            ids.append(instance.id)
    return ids

def processVideo(ec2, instance_id):
    key = paramiko.RSAKey.from_private_key_file('adithya-cloud2.pem')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    instance = [i for i in ec2.instances.filter(InstanceIds=[instance_id])][0]
    while(True):
        try:
            client.connect(hostname=instance.public_ip_address, username="ubuntu", pkey=key, timeout=30)
            print("Connecting to instance "+str(instance.id))
            sin ,sout ,serr = client.exec_command('python3 reciever.py')
            exit_status = sout.channel.recv_exit_status()
            #sin ,sout ,serr = client.exec_command('ls')
            print(exit_status)
            print(sout.read())
            print(serr.read())
            client.close()
            break
        except Exception as e:
            print("Reattempting to connect "+str(e))
            sleep(10)

def main():
    sqsQueueUrl ='https://sqs.us-east-1.amazonaws.com/416076608026/course-queue'
    awsRegion = 'us-east-1'

    ec2 = boto3.resource('ec2')
    client = boto3.client('sqs')
    threads = []
    busyIds = []

    while(True):
        print("IN while true lopp")
        # Get the length of the sqs queue
        qLength = getLengthOfQ(client,sqsQueueUrl)
        nRunning, nStopped = getNumberOfInstances(ec2)
        print(qLength,nRunning,nStopped)
        if qLength>nRunning-len(busyIds):
            stoppedIds = getStoppedIds(ec2) # Get a list of stopped instance ids
            nStart = min(nStopped, qLength-(nRunning-len(busyIds)))
            ec2.instances.filter(InstanceIds = stoppedIds[:nStart]).start()
            si = getRunningIds(ec2)
            # print("STRAt")
            # print(si)
            print("Started "+str(stoppedIds[:nStart])+" instances")
            time.sleep(30)

        # decrease instances
        elif qLength<nRunning-len(busyIds):
            runningIds = getRunningIds(ec2) # Get a list of stopped instance ids
            idleIds = [ id for id in runningIds if id not in busyIds]
            # Stop all Idle instances

            ec2.instances.filter(InstanceIds = idleIds[:len(idleIds)-qLength]).stop()
            print("Stopped "+str(idleIds[:len(idleIds)-qLength])+" instances")
            time.sleep(30)

        for runningId in getRunningIds(ec2):
            if runningId not in busyIds:
                # print("BUsy id " )
                # print(busyIds)
                t = threading.Thread(name=runningId, target = processVideo, args=(ec2, runningId))
                threads.append(t)
                busyIds.append(runningId)
                t.start()

        updated_threads = []
        for t in threads:
            if not t.is_alive():
                busyIds.remove(t.getName())
            else:
                updated_threads.append(t)

        threads = updated_threads
        sleep(30)
if __name__ == '__main__':
    main()

