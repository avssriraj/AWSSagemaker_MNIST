import csv
import boto3
import json

TABLE_NAME = 'Mnist-predict'
OUTPUT_BUCKET = 's3-assignment4'
TEMP_FILENAME = '/tmp/mnist-train.csv'
OUTPUT_KEY = 'all-mnist-train.csv'

s3_resource = boto3.resource('s3')
dynamodb_resource = boto3.resource('dynamodb')
table = dynamodb_resource.Table(TABLE_NAME)

def lambda_handler(event, context):
    with open(TEMP_FILENAME, 'w') as output_file:
        writer = csv.writer(output_file)
        header = True
        first_page = True
        while True:
            if first_page:
                response = table.scan()
                first_page = False
            else:
                response = table.scan(ExclusiveStartKey = response['LastEvaluatedKey'])

            for item in response['Items']:
                if header:
                    writer.writerow(item.keys())
                    header = False
                writer.writerow(item.values())
            if 'LastEvaluatedKey' not in response:
                break
    s3_resource.Bucket(OUTPUT_BUCKET).upload_file(TEMP_FILENAME, OUTPUT_KEY)