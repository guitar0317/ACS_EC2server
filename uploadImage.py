from __future__ import print_function
import requests
import json
import cv2
import time
import logging
from pathlib import Path
import glob
import numpy as np
import base64
import io
import os
from PIL import Image
#123sss
#test_img_folder = "D:/Fish/Fish_counting/fish_counting_system/非洲王子_25_30mm/"
def uploadImageFun():

    #addr = 'http://192.168.68.122:5000'
    #addr = 'http://localhost:5000'
    addr = 'http://ec2-54-254-127-237.ap-southeast-1.compute.amazonaws.com:5000'
    test_url = addr + '/PostImage'

    # prepare headers for http request
    content_type = 'image/jpeg'
    headers = {'content-type': content_type}

    #global test_img_folder
    #test_img_folder_path = Path(test_img_folder)
    #print("test_img_folder_path:" + str(test_img_folder_path))


    #if test_img_folder_path.is_dir():
        #test_images = Path(test_img_folder).glob('*.*')
    #files = glob.glob(r"D:\Fish\Fish_counting\fish_counting_system\Africa_25_30mm\*.png",recursive=False)
    #files = glob.glob(r"D:\Fish\Fish_counting\fish_counting_system\Africa_25_30mm\*.png",recursive=False)
    files = glob.glob(r"D:\Project\FY110\菖葳_農業科專_觀賞水族活體貿易之數位營運平臺建置\AWS\EC2\EC2_Webserver\ACS_EC2server\image\*.png",recursive=False)
    img_b64_list = []
    #param
    bw_shift = 0.0
    pix2mm_ratio = 0.8
    count_shift = 5
    frame_num = 10
    company_name="ITRI"
    devicename="D4"
    date="202203281607"
    for file in files:
        #print(str(Path(file)))
        fileName = os.path.basename(file)
        print("fileName: " + str(fileName))
        #try:
        #filePathStr = "test.jpg" 
        img64 = image_b64_Encode(file)
        #image_b64_Decode(img64)
        

        img_b64_list.append(img64)  

        
    payload = {'bw_shift': bw_shift, 'pix2mm_ratio': pix2mm_ratio, 'count_shift': count_shift,'frame_num':frame_num,'company_name':company_name, 'device_name':devicename,'date':date, 'img_list': img_b64_list}
    response = requests.post(test_url, data=payload)            
    print(json.loads(response.text))
    print("ends")  
       
  
def image_b64_Encode(imgPath): 
    im_b64 = None
    with open(imgPath, 'rb') as f:
        im_b64 = base64.b64encode(f.read())
    return im_b64


def image_b64_Decode(im_b64):
    im_binary = base64.b64decode(im_b64)
    buf = io.BytesIO(im_binary)
    img = Image.open(buf)
    #img.show()
    #cv2.imshow('imageDecode',img)
             
if __name__ == '__main__':
    uploadImageFun()