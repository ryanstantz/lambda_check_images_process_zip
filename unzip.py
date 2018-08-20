from __future__ import print_function

import urllib
import boto3
import zipfile
import json

#-------- aws variables -----------
s3_client= boto3.client('s3')
lambda_client = boto3.client('lambda')

#-------- functions begin---------
def lambda_handler(event, context):
    # Get the object from the event and show its content type
    zipped_bucket_name = event['Records'][0]['s3']['bucket']['name']
    zipped_file_key = event['Records'][0]['s3']['object']['key']

    try:
        # Download and save the zip to tmp storage
        s3_client.download_file(zipped_bucket_name, zipped_file_key,  '/tmp/file.zip')

        # Unzip the file
        unzipped = zipfile.ZipFile('/tmp/file.zip')

        # Iterate all file names and push front image files into the list of
        # files to be converted from .tif to .png and saved to our s3 check
        # images bucket
        front_image_files = []
        image_files = unzipped.namelist()
        for file in image_files:
            if file.endswith('f.tif'):
                front_image_files.insert(0, file)

        # Divide our list of images into smaller arrays of size n images
        # [1,2,3,4,5,6,7,8,9,10] -> [[1,2,3], [4,5,6], [7,8,9], [10]]
        n = 3
        split_front_images = [front_image_files[i * n:(i + 1) * n] for i in range((len(front_image_files) + n - 1) // n )]

        for front_images_chunk in split_front_images:

            payload3={
            "key": zipped_file_key,
            "bucket": zipped_bucket_name,
            "image_list": front_images_chunk
            }

            response = lambda_client.invoke(
                FunctionName="uploadImages",
                InvocationType='Event',
                Payload=json.dumps(payload3)
            )

            print("REPSPONSE")
            print(response)


    except Exception as e:
        print(e)
        print('Error unzipping {} from bucket {}.'.format(zipped_file_key, zipped_bucket_name))
        raise e
