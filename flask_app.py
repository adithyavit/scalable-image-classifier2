from flask import Flask, render_template, request, redirect, url_for
import boto3
import os 
from boto.s3.key import Key
from boto.sqs.message import Message

app = Flask(__name__)

AWS_KEY_ID =  os.environ.get("AWS_KEY_ID") 
AWS_SECRET =  os.environ.get("AWS_SECRET")
 
# print("key is")
# print(AWS_KEY_ID)

def send_to_sqs():
    s3 = boto.s3.connect_to_region(aws_region)
    s3_bucket = s3.get_bucket(bucket_name)
    sqs = boto.sqs.connect_to_region(aws_region)
    sqs_queue =  sqs.lookup(sqs_queue_name)
    
    #upload to s3
    s3_key = Key(s3_bucket)
    path_on_s3 = s3_input_prefix+"/"+uploaded_file.filename
    key.key = path_on_s3
    key.set_contents_from_filename(file_path)

    # sqs message
    msg = Message()
    messageBody = json.dumps(['process', s3_bucket, s3_prefix, s3_output_prefix, uploaded_file.filename])
    msg.set_body(msg_body)
    sqsQueue.write(msg)
    print("written to sqsQueue")



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def upload_file():
    s3 = boto3.client('s3', region_name='us-east-1', aws_access_key_id=AWS_KEY_ID, aws_secret_access_key=AWS_SECRET)
    for uploaded_file in request.files.getlist('file'):
        if uploaded_file.filename != '':
            s3.upload_fileobj(uploaded_file, 'imagebucket-adithya', uploaded_file.filename)
    
    return redirect(url_for('index'))

