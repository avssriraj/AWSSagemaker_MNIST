# Hand Written Character Recognition using AWS Sagemaker, DynamoDB and Lambda 

## System Setup:
### 1.	Bulk ingestion of csv data into DynamoDB.
I have done the bulk ingestion of the csv data into DynamoDB using CloudFormation. This CloudFormation stack loads the csv file with name “mnist-train.csv” when uploaded into the S3 bucket that is created. The attached CloudFormation template includes DynamoDB, Amazon S3, Lambda and IAM role with necessary permissions. To start with add the following policies LambdaBasicExecutionRole, AWSLambdaInvocation-DynamoDB, AmazonS3ReadOnlyAccess to the role. Provide the parameters BucketName, FileName and DynamoDBTable when creating the stack. For the DynamoDB Table name the partition key as “uuid” with Attribute type String. Use the Lambda python 3.9 code provided in the Stack as inline code. 

<img width="322" alt="image" src="https://user-images.githubusercontent.com/90299324/203173861-2afdcb33-e0de-4f6a-9796-2269bf4c79f7.png">


Challenges:
1.	The dataset doesn’t have a column that can be used as partition key.
2.	The maximum Timeout that you can provide in Lambda is 900 seconds, but the dataset has 60,000 rows and won’t finish the job before 900 seconds i.e., 15mins.

Solution:
1.	I must add a column in the dataset “uuid” and increment it from 1 to 60,000.
2.	To avoid the Lambda function from timing out I must divide the training data csv file into 2 csv files of 30,000 rows each and run the Lambda twice.

Now the DynamoDB has 60,000 items loaded with 786 columns(28x28= 784 values, 1 label value and 1 uuid value). 

### 2.	Create and load Handwritten data into DynamoDB.
To create the handwritten data, I’m using an iPad and Apple pencil to create handwritten images in Procreate. Create a 28x28 image and give it a black background and using white pencil to write numbers. Save and export the same for all numbers 0 to 9. Upload some handwritten images into a folder in the S3 bucket which can be used to predict the final sagemaker model we develop. Once uploaded in the sagemaker make the images available for prediction by clicking on Actions and selecting Make public using ACL. Sample images are displayed here.

<img width="416" alt="Screenshot 2022-11-21 at 4 50 54 PM" src="https://user-images.githubusercontent.com/90299324/203173830-456ed6de-5136-4287-b6d5-a487aece644c.png">


Create as many handwritten images as possible as. The higher the images better the training. Rename the images with the label of the image. Multiple images with same label cannot exist but make sure the first letter of the name is the label. I have written a python code named “HandwrittenToCSV.py” to create 2 csv files(1 for labels, 1 for pixel values) from the handwritten images. 

Merge the 2 csv files into one by adding labels csv file to the first column of the pixel values images. Also add a “uuid” column and increment it from 60001. 

Rename the csv file mnist-train.csv and upload the file into the S3 bucket. Once the file is uploaded the lambda function created in Step 1 by the CloudFormation stack is triggered and uploads the data in csv into DynamoDB. Since the number of items in the DynamoDB is high to confirm the uploaded items scan the number of items in DynamoDB. 

### 3.	Lambda to export the DynamoDB table to CSV and save in S3 Bucket.
Create a lambda function with Python 3.9 runtime and use the code in ExportDBToS3.py to deploy the Lambda. The same role used in Step 1 has all the policies to perform this export operation, so it can be used in this Lambda function also. This Lambda function exports the data in DynamoDB into a csv file and stores it the S3 bucket provided. Since the header of the csv file is not needed for training, I set the header to false when exporting the data. This Lambda can be automated to trigger every time a new item is added into the DynamoDB but as the amount is data is high. It is recommended to perform once the bulk ingestion and handwritten image upload is done.

Perform the same Steps 1-3 for test dataset also.


### 4.	Create Sagemaker model endpoint.
Go to AWS Sagemaker and create a sagemaker notebook instance use ml.t3.medium instance. Use the code provided in the mnist-tranferlearning.ipynb file and run all the cells. This code starts by importing all the necessary packages to train and test the mnist dataset. It also includes the creation of sagemaker endpoint instance. Hosting the Sagemaker endpoint instance is not included in the free tier. So, you are forced to use ml.c4.large instance for endpoint creation. Once run, the notebook code will create an endpoint on the sagemaker console. 
The name of my endpoint is Transfer-endpoint-202211130457


### 5.	Create a Lambda Function that calls the Sagemaker endpoint.
Create a Lambda Function to invoke Sagemaker endpoint. I named the Function Invoke-mnist-prediction-model. This Lambda function reads the image from the URL provided and converts it into array of pixels of 28x28 dimension. This array is then converted into payload which is a string of csv data just like the one in the original dataset. This payload is sent to the endpoint as a request and the response is sent back to the API. 

Create a compressed zip file using the requirements.txt(Contains only pillow) either by using Docker or Terminal. Upload the layer in Lambda Function. Use the code provided in the Invoke-mnist-prediction-model.py in the Lambda Function. You can use an existing role for this Lambda function which has access to Lambda and API Gateway. Now go to the Configuration in Lambda Function and set the Environment variable with key ENDPOINT_NAME and Value with my endpoint name i.e., Transfer-endpoint-202211130457

Challenges:
1.	This Lambda Function requires python dependencies like urllib.request to read the image from the URL and PIL to convert the image into array of values. 
2.	Often image processing python packages like matplotlib, opencv-python, scikit-image are huge python packages which even when compressed exceeds the zip file size to be uploaded as a layer in the Lambda function.

Solution:
1.	This requires you to create a layer to your Lambda function and add the python dependencies into it.
2.	As mentioned only Pillow i.e., PIL python package comes close to the file size limit. So, I used only this package. 


### 6.	Create Rest API from API Gateway.
Create a new Rest API in API Gateway console and name it MnistPredictionAPI. Use the endpoint type as Regional. Create Resources from the Actions Menu. Name the resource mnistpredict. Once the resource is created, Created a POST Method from the same Actions Menu. Select Lambda function as the Integration type. In the Lambda function enter the Lambda function created in Step 5: i.e., Invoke-mnist-prediction-model. Deploy the API from the Actions Menu and create a new stage, I named my stage prod. Click on Deploy. Save the URL obtained in this Step for testing. 


### 7.	Testing the API with Postman.
Download and install postman. You can also use postman online from chrome. 
Create a POST method use the URL obtained in Step 6 and add the resource name to the end. The URL should look something like this:
https://t2s21p8xth.execute-api.us-east-2.amazonaws.com/prod/mnistpredict
In the Body section select the raw format and provide the URL for a 28x28 image in json format. I have assumed the image to be used is a 28x28 image if the image is not in this size, We can include a resize code in the Lambda to change the size of image before sending it to the Endpoint.
{"data": "https://sagemaker-us-east-2-132656972280.s3.us-east-2.amazonaws.com/sagemaker/handwritten-numbers/IMG_0502.PNG"}

The postman request with the response is shown in figure below:


<img width="434" alt="image" src="https://user-images.githubusercontent.com/90299324/203173736-861bcc5d-9d9d-4d61-b573-adb7e52f334e.png">



Venkata Satya Sriraj Allamsetti

