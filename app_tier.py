
# commands to run the script
# cd  /home/ubuntu/classifier/
# python3 image_classification.py path_to_the_image


def process_job():
  s3Bucket = s3.get_bucket(s3BucketName)
  localInputPath = os.path.join(workDir, fileName)
  localOutputPath = os.path.join(workDir, fileName[:-5]+'.txt')
  remoteInputPath = s3InputPrefix + '/' + fileName
  remoteOutputPath = s3OutputPrefix + '/' + fileName[:-5]+'.txt'
  if not os.path.isdir(workDir):
      os.system('sudo mkdir work && sudo chmod 777 work')
  key = s3Bucket.get_key(remoteInputPath)
  s3 = boto3.client('s3')
  s3.download_file(s3BucketName, remoteInputPath, localInputPath)
  key.get_contents_to_filename(workDir+"/"+fileName)
  os.system('python3 image_classification.py '+localInputPath+' > '+localOutputPath)
  print("Uploading to s3")
  key = Key(s3Bucket)
  key.key = remoteOutputPath
  key.set_contents_from_filename(localOutputPath)
  return True

def get_sqs_jobs():
  sqs = boto.sqs.connect_to_region(aws_region)
  sqs_queue =  sqs.lookup(sqs_queue_name)
  messages = sqs_queue.get_messages(wait_time_seconds=20)
  if messages:
    for m in messages:
        job = json.loads(m.get_body())

        action = job[0]
        if action == 'process':
            s3_bucket_name = job[1]
            s3_input_prefix = job[2]
            s3_output_prefix = job[3]
            file_name = job[4]
            status = process(s3, s3_bucket_name, s3_input_prefix, s3_output_prefix, file_name, work_dir)
            if (status):
                print("Deleting message from queue as it has been successfully processed")
                m.delete()
        else:
          print("sqs queue is empty")
  
