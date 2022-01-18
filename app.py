from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime
from pymongo import MongoClient
import gridfs
import codecs
import certifi
import tensorflow as tf
import numpy as np
import os
from tensorflow.keras.preprocessing.image import ImageDataGenerator


app = Flask(__name__)
model = tf.keras.models.load_model('static/model/model.h5')
client = MongoClient('mongodb+srv://test:sparta@cluster0.5huhb.mongodb.net/Cluster0?retryWrites=true&w=majority',
                     tlsCAFile=certifi.where())
db = client.pocketmon
fs = gridfs.GridFS(db)

#################################
##  HTML을 주는 부분             ##
#################################
@app.route('/')
def home():
    return render_template('intro.html')

@app.route('/main')
def main_upload():
    return render_template('index.html')


# user 이미지 업로드
@app.route('/user_upload', methods=['POST'])
def user_upload():
    user_receive = request.form['user_give']
    file = request.files['img_give']
    fs_image_id = fs.put(file)

    doc = {
        'user_name': user_receive,
        'img': fs_image_id
    }
    db.post_img.insert_one(doc)

    file_sv = request.files['img_give_sv']
    extension = file_sv.filename.split('.')[-1]
    today = datetime.now()
    mytime = today.strftime('%Y-%m-%d-%H-%M-%S')
    filename = f'{mytime}'

    os.makedirs(f'static/img/model_check/{filename}/{filename}', exist_ok=True)
    # 파일 저장 경로 설정 (파일은 서버 컴퓨터 자체에 저장됨)
    save_to = f'static/img/model_check/{filename}/{filename}/{filename}.{extension}'
    # 파일 저장!
    file_sv.save(save_to)

    return jsonify({'result': 'success'})

@app.route('/readURL(input)/<user_title>')
def file_show(user_title):
    post_img = db.post_img.find_one({'user_name': user_title})
    img_binary = fs.get(post_img['img'])
    base64_data = codecs.encode(img_binary.read(), 'base64')
    image = base64_data.decode('utf-8')

    return render_template('index.html', img=image)



@app.route('/result')
def result():
	  # 모델은 불러와져 있으니, 사용자가 올린 데이터를 predict 함수에 넣어주면 됨
		# 이미지이기에, rescale 및 size 조정을 위해 ImageDataGenerator 활용
    last_post = list(db.post_img.find({}))[-1]
    # print(last_post)
    img_binary2 = fs.get(last_post['img'])

    base64_data2 = codecs.encode(img_binary2.read(), 'base64')
    # print(base64_data2)
    image2 = base64_data2.decode('utf-8')

    path = 'static/img/model_check'
    file_list = os.listdir(path)
    last_file_name = file_list[-1]
    test_datagen = ImageDataGenerator(rescale = 1./255)
    test_dir = f'static/img/model_check/{last_file_name}'
    test_gen = test_datagen.flow_from_directory(
      test_dir,
      target_size=(224, 224),  # (height, width)
      batch_size=1,
      seed=2021,
      class_mode='categorical',
      shuffle=False
    )
    test_imgs, test_labels = test_gen.__getitem__(0)
    testor = test_imgs[0]
    testor = (np.expand_dims(testor, 0))
    model_single = model.predict(testor)
    #여기 라벨이 나오는 부분
    result = np.argmax(model_single[0])

    result_info = db.info.find_one({'p_num': int(result)}, {})
    k_name = result_info['k_p_name']
    info_type = result_info['p_type']
    info_img = fs.get(result_info['img'])
    base64_data = codecs.encode(info_img.read(), 'base64')

    image = base64_data.decode('utf-8')

    return render_template('result.html',post_img = image2, info_img = image, info_name = k_name, type = info_type)




if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)


