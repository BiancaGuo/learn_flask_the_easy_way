from flask import render_template, Flask, redirect, url_for, request,flash
from flask_bootstrap import Bootstrap
from forms.login_form import LoginForm
from forms.watermark_form import WatermarkForm
from forms.register_form import RegisterForm
import os
from database import connect_database
from table_users import Users
from database import db
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from flask_login import login_user, login_required
from flask_login import LoginManager, current_user
from flask_login import logout_user
from flask_dropzone import Dropzone
from watermarkSystem import *
from flask import send_from_directory
import json

app=connect_database()
db.init_app(app)
bootstrap = Bootstrap(app)
dropzone = Dropzone()
dropzone.init_app(app)

# app.secret_key = os.urandom(24)
app.secret_key = "Bianca"

upload_dir=os.path.join(os.getcwd(),'upload')
upload_for_extract_dir=os.path.join(os.getcwd(),'extract_file')

if not os.path.exists(upload_dir):
    os.makedirs(upload_dir,mode=0o755)

# use login manager to manage session
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'signin'
login_manager.init_app(app=app)

# 这个callback函数用于reload User object，根据session中存储的user id
#加载用户的回调函数接受以Unicode表示的用户标志符。如果能找到用户，这个函数必须返回用户对象，否则返回None
@login_manager.user_loader
def load_user(id):
    return db.session.query(Users).get(id)

#主页
@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

#注册
@app.route('/register.html', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        '''
        if 数据库中没有该用户:存入数据库，注册成功跳转
        else： 用户已存在，跳转到登录界面
        '''
        if db.session.query(Users).filter_by(email=form.email.data).first():
            flash("该用户已存在！")
            return redirect(url_for('register'))
        else:
            user_id=db.session.query(Users).count()+1
            #加盐hash：method='pbkdf2:sha1', salt_length=8
            #session_protection可以设为None, ‘basic‘ 或‘strong‘, 以提供不同的安全等级防止用户会话遭篡改
            user = Users( id=user_id,email=form.email.data, password=generate_password_hash(form.password.data))
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('signin'))
    return render_template('register.html', form=form)

#登陆
@app.route('/signin.html', methods=['GET', 'POST'])
def signin():
    form = LoginForm()
    if form.validate_on_submit():
        flag=0
        for user in db.session.query(Users).all():
            password_hash=user.password
            if form.email.data == user.email and check_password_hash(password_hash,form.password.data):
                flag=1
                login_user(user)
                return redirect(url_for('index'))
        if flag==0:
            flash("邮箱或密码错误，请重新登录！")
            return redirect(url_for('signin'))
    return render_template('signin.html', form=form)

#登出
@app.route('/signout.html', methods=['GET', 'POST'])
def signout():
    logout_user()
    return redirect(url_for('index'))

#添加水印——上传文件
files=[]#上传文件路径
@app.route('/upload', methods=['GET','POST'])
@login_required #保护某些路由只让认证用户访问
def upload():
    if request.method == 'POST':  # 如果请求类型为POST，说明是文件上传请求
        f = request.files.get('file')  # 获取文件对象
        if f.filename.split('.')[len(f.filename.split('.'))-1] not in [ 'png','jpg','jpeg','bmp','mp3','mp4','wav','mxf']:
            return '上传格式仅限图片、音频、视频!', 400
        f.save(os.path.join(upload_dir, f.filename))  # 保存文件
        files.append(os.path.join(upload_dir, f.filename))
        return redirect(url_for('add_watermark'))
    return 'upload template'  # 渲染上传页面

#添加水印
@app.route('/add_watermark.html', methods=['GET', 'POST'])
@login_required
def add_watermark():
    maps = []
    form = WatermarkForm()
    if form.validate_on_submit():
        for file in files:
            list = file.split('.')
            if list[len(list)-1] in ['png', 'jpg', 'jpeg', 'bmp']:
                file_name = file.split("\\")[-1] + "_embed.bmp"
                maps.append(file_name)
                watermark("image", "embed", file, form.watermark.data)
            if list[len(list)-1] in ['wav']:
                file_name = file.split("\\")[-1] + "_embed.wav"
                maps.append(file_name)
                watermark("audio", "embed", file, form.watermark.data)
            if list[len(list)-1] in ['mxf']:
                file_name = file.split("\\")[-1] + "_embed.ts"
                maps.append(file_name)
                watermark("video", "embed", file, form.watermark.data)
        for file in files:
            if file.split('.')[len(file.split('.'))-1] in ['png', 'jpg', 'jpeg', 'bmp']:
                os.remove(file.split("\\")[-1]+".bmp")
        flash("请点击下载：")
        files.clear()
        file_handle = open('upload_file.txt', mode='w')
        for m in maps:
            file_handle.write(m)
            file_handle.write('\n')
        file_handle.close()
        return redirect(url_for('filelist'))
    return render_template('add_watermark.html', form=form)

#含水印文件列表
@app.route('/filelist')
@login_required
def filelist():
    maps=[]
    file_handle = open("upload_file.txt",mode='r')
    while True:
        contents = file_handle.readline()
        if contents == '':
            break
        maps.append(contents)
    file_handle.close()
    return render_template('add_watermark.html', files=maps)

#文件下载
@app.route('/download/<filename>',methods=['GET'])
@login_required
def download(filename):
    embed_dir = os.path.join(os.getcwd(), 'embed_file')
    return send_from_directory(embed_dir, filename, mimetype='application/octet-stream')

#提取水印——上传文件
extract_files=[]
@app.route('/upload_for_extract', methods=['GET','POST'])
@login_required
def upload_for_extract():
    if request.method == 'POST':  # 如果请求类型为POST，说明是文件上传请求
        f = request.files.get('file')  # 获取文件对象
        list=f.filename.split('.')
        if list[len(list)-1] not in [ 'png','jpg','jpeg','bmp','mp3','mp4','wav','mxf']:
            return '上传格式仅限图片、音频、视频!', 400
        f.save(os.path.join(upload_for_extract_dir, f.filename))  # 保存文件
        extract_files.append(os.path.join(upload_for_extract_dir, f.filename))
        return redirect(url_for('extract_watermark'))
    return 'upload_for_extract template'  # 渲染上传页面

#提取水印
@app.route('/extract_watermark.html', methods=['GET','POST'])
@login_required
def extract_watermark():
    maps = {}
    form = WatermarkForm()
    if form.validate_on_submit():
        for file in extract_files:
            list = file.split('.')
            if list[len(list)-1] in ['png', 'jpg', 'jpeg', 'bmp']:
                file_name = file.split("\\")[-1]
                result=watermark("image", "extract", file)
                maps[file_name]=result
            if list[len(list)-1] in ['wav']:
                file_name = file.split("\\")[-1]
                result = watermark("audio", "extract", file)
                maps[file_name] = result
            if list[len(list)-1] in ['mxf']:
                file_name = file.split("\\")[-1]
                result = watermark("video", "extract", file)
                maps[file_name] = result
        flash("水印提取结果为：")
        extract_files.clear()
        js = json.dumps(maps)
        file = open('extract_file.txt', 'w')
        file.write(js)
        file.close()
        return redirect(url_for('filelist2'))
    return render_template('extract_watermark.html', form=form)

#提取水印信息列表
@app.route('/filelist2')
@login_required
def filelist2():
    file = open('extract_file.txt', 'r')
    js = file.read()
    maps = json.loads(js)
    file.close()
    return render_template('extract_watermark.html', files=maps)

if __name__ == '__main__':    
    app.run(debug=True)