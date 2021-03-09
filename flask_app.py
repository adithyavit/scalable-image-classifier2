from flask import Flask, render_template, request, redirect, url_for
import json
import boto3
import boto
import os 
from boto.s3.key import Key
from boto.sqs.message import Message

app = Flask(__name__)

# AWS_KEY_ID =  os.environ.get("AWS_KEY_ID") 
# AWS_SECRET =  os.environ.get("AWS_SECRET")
 
# print("key is")
# print(AWS_KEY_ID)

def send_to_sqs(awsRegion, s3BucketName, sqsQueueName, uploaded_file, s3InputPrefix, s3OutputPrefix,localPath, s3, sqs):
    # s3.upload_fileobj(uploaded_file, bucket_name, uploaded_file.filename)
    
    # sqs.send_message(QueueUrl='https://sqs.us-east-1.amazonaws.com/416076608026/course-queue', MessageBody='hello')

    # s3 = boto.s3.connect_to_region(awsRegion)
    # s3Bucket = s3.get_bucket(s3BucketName)

    sqs = boto.sqs.connect_to_region(awsRegion)
    sqsQueue =  sqs.lookup(sqsQueueName)
    remotePath = s3InputPrefix + '/' + uploaded_file.filename #fileName[1]
    print("Uploading %s to s3://%s/%s ..." % (localPath, s3BucketName, remotePath))

    # key = Key(s3Bucket)
    # key.key = remotePath
    # key.set_contents_from_filename(localPath)
    print(type(str(uploaded_file.filename)))
    s3.upload_fileobj(uploaded_file, "imagebucket-adithya-inputfolder", str(uploaded_file.filename))

    print("Sending message to SQS queue ...")
    messageBody = json.dumps(['process', s3BucketName, s3InputPrefix, s3OutputPrefix, uploaded_file.filename])
    print(str(messageBody))
    m = Message()
    m.set_body(messageBody)
    print(m)
    sqsQueue.write(m)
    print("Done!")


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def upload_file():
    aws_region = "us-east-1"
    bucket_name = "imagebucket-adithya"
    sqs_queue_name = "course-queue"
    # s3 = boto3.resource('s3')
    s3 = boto3.client('s3')
    sqs = boto3.resource('sqs')
    for uploaded_file in request.files.getlist('file'):
        print(uploaded_file)
        if uploaded_file.filename != '':
            # s3.upload_fileobj(uploaded_file, 'imagebucket-adithya', uploaded_file.filename)
            send_to_sqs(aws_region, bucket_name, sqs_queue_name, uploaded_file, "inputfolder", "outputfolder", uploaded_file.filename, s3, sqs)
            print(type(uploaded_file.filename))
            
    return redirect(url_for('index'))


"""@app.route('/', methods=['POST'])
def upload_file():
    sqs = boto3.client('sqs', region_name='us-east-1', aws_access_key_id=AWS_KEY_ID, aws_secret_access_key=AWS_SECRET)
    sqs.send_message(QueueUrl='https://sqs.us-east-1.amazonaws.com/416076608026/course-queue', MessageBody='hello')
    return redirect(url_for('index'))
    
"""