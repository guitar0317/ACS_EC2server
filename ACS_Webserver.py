from distutils.log import debug
from http import client
from flask import Flask, request, Response
from flask import jsonify
import requests
import boto3
from botocore.exceptions import ClientError
from os import listdir
from os.path import isfile, isdir, join
import datetime
import base64
import io
import numpy
import cv2
from PIL import Image
import json
import requests.packages.urllib3

#ip = "ec2-54-254-127-237.ap-southeast-1.compute.amazonaws.com"  #IP address of Amazon EC2
ip = "localhost" #IP for test

#Access permission of IAM roel 
access_key = 'AKIAS2OTXTXV32WRBZ4P'
access_secret = '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'

#relevant parameters of counting algorithm
bw_shift=0.0
pix2mm_ratio=0.0
count_shift=0
frame_num=5
company_name="D"
device_name="D3"
date="20220216140422"
bucket_name="cwaacs" # Bucket name of Amazon S3

#WebServer
flaskobj = Flask(__name__)
@flaskobj.route("/",methods=["GET"]) #Get method...is a test
def helloTest():
    result = {
        "Sussce" :True,
        "message": "Hello world!"
    }
    return jsonify(result)

# APP上傳後端參數
# 1. img_list：依照參數設定的影像數量來取像放入list，目前用base64編碼
# 2. bw_shift: 值範圍:0-50  (step: 0.1)   
# 3. pix2mm_ratio:值範圍: 0-5(step:0.1)   
# 4. count_shift:值範圍:-30~+30 (step:1)
# 5. frame_num:取得影像張數範圍：0~100(step:1)
# 6. company_name:公司名稱
# 7. device_name:裝置名稱
# 8. date:日期時間(YYYYMMDDHHmmss)

# 後端回傳APP參數
# 1. success:辨識運算成功與否ture or false(bool)
# 2. message:辨識運算失敗錯誤訊息(請加在UI上)
# 3. count_result:水族生物計數數量
# 4. avg_length:水族生物平均體長
# 5. result_img:結果影像URL
# 6. compute_time:辨識運行時間(請加在UI，單位是秒sec)
Image_List = []
Lambda_client = None
@flaskobj.route("/PostImage", methods=["POST"]) #Post method...is main 
def PostImage_amount_couting():
    try:
        payload = request.form.to_dict(flat=False)
        bw_shift = payload["bw_shift"][0]
        pix2mm_ratio = payload['pix2mm_ratio'][0]
        count_shift = payload['count_shift'][0]
        frame_num = payload["frame_num"][0]
        company_name=payload["company_name"][0]
        device_name=payload["device_name"][0]
        date=payload["date"][0]
        img_list = payload['img_list']  #Image
        # print("bw_shift:"+str(bw_shift))
        # print("count_shift:"+str(count_shift))
        # print("frame_num:"+str(frame_num))
        # print("company_name:"+str(company_name))
        # print("device_name:"+str(device_name))
        # print("date:"+str(date))
        S3path= company_name+'/'+device_name+'/'+date+'/original/'
        requests.packages.urllib3.disable_warnings()
        a ={
             "key1": "value1",
             "key2": "value2",
             "key3": "value3"
         }
        Lambda_client = boto3.client('lambda',region_name='ap-southeast-1',verify=False ,aws_access_key_id = access_key, aws_secret_access_key = access_secret)
        response = Lambda_client.invoke(
             FunctionName='arn:aws:lambda:ap-southeast-1:194254446059:function:CallTest',
             #FunctionName='CallTest',
            #  InvocationType='Event',
             InvocationType='RequestResponse',
             LogType='None',
             ClientContext='None',
             Payload= base64.b64encode(json.dumps(a))
             )
        print(response)
        #print("S3 Path="+S3path)
        # for index,im_b64 in enumerate(img_list):
        #      im_binary = base64.b64decode(im_b64)    
        #      buf = io.BytesIO(im_binary)
        #      # pilImg = Image.open(buf)
        #      # #pilImg.show()
        #      # numpyImg = numpy.asarray(pilImg)
        #      # img = cv2.cvtColor(numpyImg,cv2.COLOR_RGB2BGR) 
        #      # cv2.imshow("A",img)
        #      # cv2.waitKey(0)
        #      #cv2.imwrite(str(index)+".png",img)
        #      Upload_file(S3path, buf, S3path+str(index))
 
        # if Upload_file(S3path):
        #     print("Susscess")
        # else:
        #     print("Fail")
        # result = {
        # "sussce" :True,
        # "message": "Success"
        # "count_result"
        # "avg_lengt"
        # "result_img"
        # "compute_time":
        # }    
        result = {
        "sussce" :True,
        "message": "Sucess"
        }   
        return jsonify(result)
    except Exception as e:
        print(e)
        result = {
        "sussce" :False,
        "message": e
        }
        return jsonify(result)

s3_client = None
#Creating a bucket of S3, then get entire bucket into to list
def Create_S3_bucket(): 
    s3_client = boto3.client('s3', verify=False ,aws_access_key_id = access_key, aws_secret_access_key = access_secret)
    s3_client.create_bucket(
    ACL='public-read',
    Bucket='hellojared',
    CreateBucketConfiguration={'LocationConstraint': 'ap-southeast-1'},
    GrantFullControl='hellojared'
    ) 
    response = s3_client.list_buckets()
    bucketsList= response['Buckets']
        # Output the bucket names
    print('Existing buckets:')
    for bucket in bucketsList:
        bucketName = bucket["Name"]
        print(bucketName)

#Uploading file to bucket   
# filepath='D:/Python_EX/image/'
def Upload_file(S3path, image, index):
    try:
        # img = Image.fromarray(image)
        # buffer = io.BytesIO()
        # img.save(buffer, format="PNG")
        # hex_data = buffer.getvalue()
        s3_client = boto3.client('s3', verify=False ,aws_access_key_id = access_key, aws_secret_access_key = access_secret)
        #s3_client.put_object(Bucket=bucket_name, Key=index+'.png', Body=hex_data,  ACL="public-read")
        s3_client.upload_fileobj(image, bucket_name,index+'.png',ExtraArgs={'ACL': 'public-read'})
        #image = os.path.basename(filepath)
        #image = listdir(filepath)
        #print(image)
        #using object method
        # for i in image:
        #     filename = filepath+i
        #     with open(filename,mode="rb") as file: 
        #         s3_client.upload_fileobj(file, bucket_name, S3path+i,ExtraArgs={'ACL': 'public-read'})
        # print(file)
        #using filename method
        # for i in range(0,len(image),1):
        #     print(join(filepath+image[i]))
        #     s3_client.upload_file(filepath+image[i], bucket_name, S3path+image[i],ExtraArgs={'ACL': 'public-read'})
        return True
    except ClientError as e:
        print(e)
        return False
    return True

#Program main(entry)
if __name__ == '__main__':
    print('Flask start')
    print('flask ip address=' + ip)
    flaskobj.run(ip, debug=True, port=5000, use_reloader=False)
    #date = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    # S3path= company_name+'/'+device_name+'/'+date+'/original/'
    # print("S3 Path="+S3path)
    # if Upload_file(S3path):
    #     print("Susscess")
    # else:
    #     print("Fail")
    #Create_S3_bucket(path)
  

