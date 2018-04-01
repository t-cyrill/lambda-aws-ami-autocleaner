import os
import boto3
import logging
from operator import itemgetter, attrgetter

images_limit = os.environ['NUM_OF_IMAGE']
code_pipeline = boto3.client('codepipeline')

def lambda_handler(event, context):
  logger = logging.getLogger()
  logger.setLevel(logging.INFO)

  session = boto3.Session()
  ec2_client = session.client('ec2')

  images = ec2_client.describe_images(Owners=["self"], Filters=[{"Name": "tag:autoclean", "Values": ["true"]}])
  delta_image_num = len(images["Images"]) - images_limit
  if delta_image_num > 0:
    for i in range(delta_image_num):
      image = sorted(images["Images"], key = itemgetter("CreationDate"))[i]
      ec2_client.deregister_image(ImageId=image["ImageId"])
      logger.info("Deregister Image:" + image["ImageId"])
      ec2_client.delete_snapshot(SnapshotId=image["BlockDeviceMappings"][0]["Ebs"]["SnapshotId"])
      logger.info("Delete SnapShot:" + image["BlockDeviceMappings"][0]["Ebs"]["SnapshotId"])
  else:
      logger.info("len(images) " + str(len(images["Images"])) + " < " + str(images_limit) + ".")
  code_pipeline.put_job_success_result(jobId=event['CodePipeline.job']['id'])
  return "Complete."

