from distutils.log import debug
from http import client
import io
from flask import Flask, request, Response
from flask import jsonify
import requests
import boto3
from botocore.exceptions import ClientError
from os import listdir
from os.path import isfile, isdir, join
import datetime
import base64
import numpy
from PIL import Image
import json
import requests.packages.urllib3

ip = "ec2-54-254-127-237.ap-southeast-1.compute.amazonaws.com"  #IP address of Amazon EC2
#ip = "localhost" #IP for test

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
        S3path= company_name+'/'+device_name+'/'+date#+'/original/'
        requests.packages.urllib3.disable_warnings() #避免SSL驗證 
        # print("bw_shift:"+str(bw_shift))
        # print("count_shift:"+str(count_shift))
        # print("frame_num:"+str(frame_num))
        # print("company_name:"+str(company_name))
        # print("device_name:"+str(device_name))
        # print("date:"+str(date))
        
        #逐一將影像上傳至S3
        for index,im_b64 in enumerate(img_list):
              im_binary = base64.b64decode(im_b64)    
              buf = io.BytesIO(im_binary)
        #      # pilImg = Image.open(buf)
        #      # #pilImg.show()
        #      # numpyImg = numpy.asarray(pilImg)
        #      # img = cv2.cvtColor(numpyImg,cv2.COLOR_RGB2BGR) 
        #      # cv2.imshow("A",img)
        #      # cv2.waitKey(0)
        #      #cv2.imwrite(str(index)+".png",img)
              Upload_file(S3path+'/original/', buf, S3path+'/original/'+str(index))
        print("Images were uploaded to "+ bucket_name+'/'+S3path)
        S3path = 's3://'+bucket_name+'/'+S3path
        #Call lambda(fish counting)
        lambda_parameter ={
             "bw_shift": bw_shift,
             "pix2mm_ratio":pix2mm_ratio,
             "count_shift": count_shift,
             "frame_num": frame_num,
            #  "company_name":company_name,
            #  "device_name":device_name,
            #  "date":date,
             "bucket_name":bucket_name,
             "img_path": S3path
         }
        lambda_flag, response = Lambda_Invoke(lambda_parameter)
        if lambda_flag:
            print("Counting was finished. StatusCode="+str(response["StatusCode"]))
            # #print(str(response["StatusCode"]))
            temp = json.load(response["Payload"])
            if temp["success"] == False:
                print(temp["message"])
                result = {
                    "success" :False,
                    "message": temp["message"],
                } 
            else:   
                result = {
                    "success" :True,
                    "message": "Success",
                    "count_result":temp["count_result"],
                    "avg_length":temp["avg_length"],
                    "result_img":temp["result_img"],
                    "compute_time":temp["compute_time"]
                } 
        else:
            print("Call lmabda fail.")
            print(response["message"])
            result = {
                "sussce" :False,
                "message": response["message"]
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
def Upload_file(S3path, image, index):
    try:
        s3_client = boto3.client('s3', verify=False ,aws_access_key_id = access_key, aws_secret_access_key = access_secret)
        s3_client.upload_fileobj(image, bucket_name,index+'.png',ExtraArgs={'ACL': 'public-read'})
        # img = Image.fromarray(image)
        # buffer = io.BytesIO()
        # img.save(buffer, format="PNG")
        # hex_data = buffer.getvalue()     
        #s3_client.put_object(Bucket=bucket_name, Key=index+'.png', Body=hex_data,  ACL="public-read")
        return True
    except ClientError as e:
        print(e)
        return False
    return True

def Lambda_Invoke(parameter):
    try:
        Lambda_client = boto3.client('lambda',region_name='ap-southeast-1',verify=False ,aws_access_key_id = access_key, aws_secret_access_key = access_secret)
        response = Lambda_client.invoke( #call lambda function
            FunctionName='arn:aws:lambda:ap-southeast-1:194254446059:function:FishCounting',
            #FunctionName='arn:aws:lambda:ap-southeast-1:194254446059:function:CallTest',
                #FunctionName='CallTest',
                #InvocationType='Event',
            InvocationType='RequestResponse',
            LogType='None',
                #ClientContext='None',
                #Payload= base64.b64encode(json.dumps(a).encode("utf-8"))
            Payload = json.dumps(parameter)
        )
        return True, response
    except Exception as e:
        print(e)
        result = {
        "sussce" :False,
        "message": e
        }
        return False, jsonify(result)


#Program main(entry)
if __name__ == '__main__':
    print("WebServer start...")
    print('WebServer ip address = ' + ip)
    flaskobj.run(ip, debug=True, port=5000, use_reloader=False)
    #date = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    # S3path= company_name+'/'+device_name+'/'+date+'/original/'
    # print("S3 Path="+S3path)
    # if Upload_file(S3path):
    #     print("Susscess")
    # else:
    #     print("Fail")
    #Create_S3_bucket(path)
  

