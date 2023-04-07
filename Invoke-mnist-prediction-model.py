import os
import io
import boto3
import json
import csv
from urllib.request import urlopen
from io import BytesIO
from PIL import Image


# grab environment variables
ENDPOINT_NAME = os.environ['ENDPOINT_NAME']
runtime= boto3.client('runtime.sagemaker')

def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))
    
    data = json.loads(json.dumps(event))
    payload = data['data']
    
    response = urlopen(payload)
    buf = BytesIO(response.read())
    im = Image.open(buf)
    im = im.convert('L')
    pixels = list(im.getdata())
    payload = ','.join(str(item) for item in pixels)
    response = runtime.invoke_endpoint(EndpointName=ENDPOINT_NAME,
                                       ContentType='text/csv',
                                       Body=payload)
    print(response)
    result = json.loads(response['Body'].read().decode())
    print(result)
    pred = int(result['predictions'][0]['score'])
    predicted_label = pred
    
    return predicted_label
