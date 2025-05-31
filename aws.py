import os
import boto3

s3_client = boto3.client("s3")
s3_resource = boto3.resource("s3")

response = s3_client.list_buckets()

for bu in response["Buckets"]:
    print(bu)


response = s3_client.list_objects_v2(Bucket = 'motion-camera-storage')

objects = response.get("Contents",[])

print(objects)

s3_client.download_file(Bucket = "motion-camera-storage" , Key = 'React_notes.docx', Filename = "file1downlaod.docx")