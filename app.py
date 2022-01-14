from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime
from pymongo import MongoClient
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import tensorflow as tf
import numpy as np

import os
import gridfs
import codecs
import certifi

model = tf.keras.models.load_model('static/model/model.h5')

app = Flask(__name__)

client = MongoClient('mongodb+srv://test:sparta@cluster0.5huhb.mongodb.net/Cluster0?retryWrites=true&w=majority',
                     tlsCAFile=certifi.where())
db = client.pocketmon
fs = gridfs.GridFS(db)


#################################
##  HTML을 주는 부분             ##
#################################
@app.route('/')
def home():
    return render_template('index.html')


# 포켓몬 정보 db 저장
@app.route('/info_save', methods=['POST'])
def info_save():
    name_receive = request.form['name_give']
    k_name_receive = request.form['k_name_give']
    p_num_receive = request.form['p_num_give']
    file = request.files['file_give']
    # gridfs 활용해서 이미지 분할 저장
    fs_image_id = fs.put(file)

    # db 추가
    doc = {
        'p_name': name_receive,
        'k_p_name': k_name_receive,
        'p_num': p_num_receive,
        'img': fs_image_id
    }
    db.info.insert_one(doc)

    return jsonify({'result': 'success'})


# user 이미지 업로드
@app.route('/user_upload', methods=['POST'])
def user_upload():
    user_receive = request.form['user_give']
    img = request.files['img_give']
    # gridfs 활용해서 이미지 분할 저장
    fs_image_id = fs.put(img)

    extension = img.filename.split('.')[-1]
    today = datetime.now()
    mytime = today.strftime('%Y-%m-%d-%H-%M-%S')
    filename = f'{mytime}'
    os.makedirs(f'static/img/model_check/{filename}/{filename}', exist_ok=True)
    # 파일 저장 경로 설정 (파일은 서버 컴퓨터 자체에 저장됨)
    save_to = f'static/img/model_check/{filename}/{filename}/{filename}.{extension}'
    # 파일 저장!
    img.save(save_to)

    # db 추가
    doc = {
        'user_name': user_receive,
        'img': fs_image_id
    }
    db.post_img.insert_one(doc)

    return jsonify({'result': 'success'})

#
# @app.route('/usershow/<user_title>')
# def file_show(user_title):
#
#     post_img = db.post_img.find_one({'user_name': user_title})
#     img_binary = fs.get(post_img['img'])
#
#     base64_data = codecs.encode(img_binary.read(), 'base64')
#     image = base64_data.decode('utf-8')
#
#     return render_template('index.html', img=image)

# user 업로드 전에 미리보기
@app.route('/readURL(input)/<user_title>')
def file_show(user_title):
    post_img = db.post_img.find_one({'user_name': user_title})
    img_binary = fs.get(post_img['img'])
    base64_data = codecs.encode(img_binary.read(), 'base64')
    image = base64_data.decode('utf-8')

    return render_template('index.html', img=image)


@app.route('/result')
def result():
    path = 'static/img/model_check'
    file_list = os.listdir(path)
    last_file_name = file_list[-1]
    test_datagen = ImageDataGenerator(rescale=1. / 255)
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
    # 여기 라벨이 나오는 부분
    result = np.argmax(model_single[0])
    # DB에서 라벨 기준으로 기본정보 불러올것 붙이면 됨

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
