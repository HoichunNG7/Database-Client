from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from math import ceil
import http.cookies
import json
import sqlite3
import base64
import time

# 错误提示信息汇总
existUser = {'error': 'user exists'}  # 注册输入用户已存在
invalidParam = {'error': 'invalid parameters'}  # 参数为空或者非法
illegalAccess = {'error': 'no valid session'}  # 非法访问,eg. wrong session_id
illegalName = {'error': 'need name words'}  # URL参数'name'不存在或者为空
loggedIn = {'error': 'has logged in'}  # 已处于登录状态
nonexistentUser = {'error': 'no such a user'}  # 用户名参数为空 or 用户不存在
requireLogin = {'error': 'please login'}  # 尚未登录
typePOST = {'error': 'require POST'}  # 应为POST请求
unknownRecord = {'error': 'unknown record'}  # 记录不存在/不属于当前用户
unknownField = {'error': 'unknown record field'}  # 请求正文中存在未知字段
wrongPw = {'error': 'password is wrong'}  # 密码不正确

# 各接口对应网页汇总
logon_page = '''<form action="/logon" method="post">
Username:<input type="text" name="username" value="%s"/></br>
Password:<input type="password" name="password" value="%s"/></br>
<input type="submit" value="Submit"/>
</form>
'''
login_page = '''<form action="/login" method="post">
Username:<input type="text" name="username" value="%s"/></br>
Password:<input type="password" name="password" value="%s"/></br>
<input type="submit" value="Login"/>
</form>
'''
add_record_page = '''<form action="/record/add" method="post">
Name:<input type="text" name="name" value="%s"/></br>
TimeStamp:<input type="text" name="timestamp" value="%s"/></br>
Content:<input type="text" name="content" value="%s"/></br>
<input type="submit" value="Add Record"/>
</form>
'''

update_record_page = '''<form action="/record/%s/update" method="post">
Name:<input type="text" name="name" value="%s"/></br>
TimeStamp:<input type="text" name="timestamp" value="%s"/></br>
Content:<input type="text" name="content" value="%s"/></br>
<input type="submit" value="Update Record"/>
</form>
'''


# 后台处理辅助函数
def judge_user_exist(user_name, pw):  # 判断注册输入用户是否已存在
    conn = sqlite3.connect('onlineDB.db')
    user_cursor = conn.cursor()

    user_cursor.execute('select * from user where username=?', (user_name,))
    user = user_cursor.fetchall()

    # 不存在时存储当前用户
    if not user:
        pw = base64.b64encode(pw.encode('ascii'))
        stored_pw = pw.decode('ascii')
        user_cursor.execute("insert into user (username, password) values ('%s','%s')" % (user_name, stored_pw))

    user_cursor.close()
    conn.commit()
    conn.close()
    if user:
        return True
    else:
        return False


def find_db_user(user_name, pw):  # 在数据库中寻找登录输入用户
    conn = sqlite3.connect('onlineDB.db')
    user_cursor = conn.cursor()

    user_cursor.execute('select * from user where username=?', (user_name,))
    user = user_cursor.fetchall()

    user_cursor.close()
    conn.commit()
    conn.close()

    if not user:  # 用户不存在
        return 0
    else:
        pw = base64.b64encode(pw.encode('ascii'))
        stored_pw = pw.decode('ascii')
        if user[0][1] != stored_pw:  # 密码不正确
            return 1
        else:  # 无异常
            return 2


def create_session_id(user_name, pw):  # 生成Cookies中的session_id
    user_name = base64.b64encode(user_name.encode('ascii'))
    encrp_id = user_name.decode('ascii')  # 加密用户名
    pw = base64.b64encode(pw.encode('ascii'))
    encrp_pw = pw.decode('ascii')  # 加密密码

    half_length = ceil(len(encrp_pw) / 2)
    str_hl = str(half_length)
    if len(str_hl) == 1:
        str_hl = '0' + str_hl

    session_id = str_hl + encrp_pw[0:half_length] + encrp_id
    return session_id


def verify_session_id(cookie):  # 校验Cookies中的session_id是否合法
    str_hl = cookie[0:2]
    half_length = 0
    if str_hl[0] == '0':
        half_length = int(str_hl[1])
    else:
        half_length = int(str_hl)

    cookie = cookie[2:]
    half_password = cookie[0:half_length]
    user_name = base64.b64decode(cookie[half_length:].encode('ascii')).decode('ascii')

    # 访问数据库
    conn = sqlite3.connect('onlineDB.db')
    user_cursor = conn.cursor()
    user_cursor.execute('select * from user where username=?', (user_name,))
    user = user_cursor.fetchall()
    user_cursor.close()
    conn.close()

    if not user:
        return False
    if user[0][1][0:half_length] == half_password:
        return user_name
    else:
        return False


# Create your views here.
def index(request):
    return HttpResponse('Hello!')


@csrf_exempt
def logon(request):  # 注册

    if 'username' in request.POST:
        username = request.POST['username']
        password = request.POST['password']
    else:
        username = ''
        password = ''
        return HttpResponse(logon_page % (username, password))

    # 异常处理
    if request.method == 'GET':
        return HttpResponse(json.dumps(typePOST), content_type="application/json")

    if not username or not password:
        return HttpResponse(json.dumps(invalidParam), content_type="application/json")
    elif judge_user_exist(username, password):
        return HttpResponse(json.dumps(existUser), content_type="application/json")
    else:  # 无异常
        user_info = {'user': username}
        return HttpResponse(json.dumps(user_info), content_type="application/json")


@csrf_exempt
def login(request):  # 登录
    if 'username' in request.POST:
        username = request.POST['username']
        password = request.POST['password']
    else:
        username = ''
        password = ''
        return HttpResponse(login_page % (username, password))

    # 异常处理
    if request.method == 'GET':
        return HttpResponse(json.dumps(typePOST), content_type="application/json")

    status = find_db_user(username, password)
    if status == 0:  # 用户不存在
        return HttpResponse(json.dumps(nonexistentUser), content_type="application/json")
    elif status == 1:  # 密码不正确
        return HttpResponse(json.dumps(wrongPw), content_type="application/json")
    elif status == 2:
        cookie_id = request.COOKIES.get('session_id')
        if cookie_id:  # 已处于登录状态
            if verify_session_id(cookie_id):  # *Cookies正常
                return HttpResponse(json.dumps(loggedIn), content_type="application/json")
            else:  # *Cookies内容异常
                return HttpResponse(json.dumps(illegalAccess), content_type="application/json")
        else:  # 无异常，登录并分配session_id
            new_id = create_session_id(username, password)  # 生成新的session_id
            user_info = {'user': username}
            login_response = HttpResponse(json.dumps(user_info))
            login_response.set_cookie('session_id', new_id)  # 不设置过期时间
        return login_response


@csrf_exempt
def logout(request):  # 注销
    # 异常处理
    if request.method == 'GET':
        return HttpResponse(json.dumps(typePOST), content_type="application/json")

    cookie_id = request.COOKIES.get('session_id')
    if not cookie_id:  # 没有Cookies
        return HttpResponse(json.dumps(illegalAccess), content_type="application/json")
    else:  # 有Cookies
        if verify_session_id(cookie_id):  # Cookies有效
            user_info = { 'user': 'nothing' }
            user_info['user'] = verify_session_id(cookie_id)
            logout_response = HttpResponse(json.dumps(user_info))
            logout_response.delete_cookie('session_id')
            return logout_response
        else:  # Cookies无效
            return HttpResponse(json.dumps(illegalAccess), content_type="application/json")


@csrf_exempt
def add_record(request):  # 增加记录
    if 'name' in request.POST:
        name = request.POST['name']
        timestamp = request.POST['timestamp']
        content = request.POST['content']
    else:
        name = ''
        timestamp = ''
        content = ''
        return HttpResponse(add_record_page % (name, timestamp, content))

    # 异常处理
    cookie_id = request.COOKIES.get('session_id')
    if not cookie_id:  # 没有Cookies，尚未登录
        return HttpResponse(json.dumps(requireLogin), content_type="application/json")
    elif not name or not timestamp or not content:  # name/timestamp/content为空
        return HttpResponse(json.dumps(invalidParam), content_type="application/json")
    elif not timestamp.isdigit():  # timestamp不为正整数
        return HttpResponse(json.dumps(invalidParam), content_type="application/json")

    user = verify_session_id(cookie_id)

    # 添加到数据库
    conn = sqlite3.connect('onlineDB.db')
    user_cursor = conn.cursor()
    user_cursor.execute("insert into data (name,timestamp,content, user) values ('%s','%s','%s','%s')"
                        % (name, timestamp, content, user))
    conn.commit()
    user_cursor.execute('select id from data where name=?', (name,))
    record_id = user_cursor.fetchall()  # 获取当前记录分配id
    user_cursor.close()
    conn.close()

    data_info = {'record_id': '1'}
    data_info['record_id'] = record_id[0][-1]
    return HttpResponse(json.dumps(data_info), content_type="application/json")


@csrf_exempt
def delete_record(request, offset):  # 删除记录
    # 异常处理
    cookie_id = request.COOKIES.get('session_id')
    if not cookie_id:  # 没有Cookies，尚未登录
        return HttpResponse(json.dumps(requireLogin), content_type="application/json")
    elif request.method != 'POST':  # 请求方式不是POST
        return HttpResponse(json.dumps(typePOST), content_type="application/json")
    elif not offset.isdigit() or offset[0] == '0':  # id不是正整数
        return HttpResponse(json.dumps(invalidParam), content_type="application/json")

    user = verify_session_id(cookie_id)

    # 访问数据库
    conn = sqlite3.connect('onlineDB.db')
    user_cursor = conn.cursor()
    user_cursor.execute('select * from data where id=?', (int(offset),))
    record = user_cursor.fetchall()  # 获取指定记录

    if not record or record[0][-1] != user:  # 记录不存在/不属于当前用户
        return HttpResponse(json.dumps(unknownRecord), content_type="application/json")

    user_cursor.execute('delete from data where id=?', (int(offset),))
    conn.commit()

    user_cursor.close()
    conn.close()

    data_info = {'record_id': '12'}
    data_info['record_id'] = int(offset)
    return HttpResponse(json.dumps(data_info), content_type="application/json")


@csrf_exempt
def update_record(request, offset):  # 修改记录
    if 'name' in request.POST or 'timestamp' in request.POST or 'content' in request.POST:
        if 'name' in request.POST:
            name = request.POST['name']
        else:
            name = ''
        if 'timestamp' in request.POST:
            timestamp = request.POST['timestamp']
        else:
            timestamp = ''
        if 'content' in request.POST:
            content = request.POST['content']
        else:
            content = ''
    else:
        name = ''
        timestamp = ''
        content = ''
        return HttpResponse(update_record_page % (offset, name, timestamp, content))

    # 异常处理
    cookie_id = request.COOKIES.get('session_id')
    if not cookie_id:  # 没有Cookies，尚未登录
        return HttpResponse(json.dumps(requireLogin), content_type="application/json")
    elif request.method != 'POST':  # 请求方式不是POST
        return HttpResponse(json.dumps(typePOST), content_type="application/json")
    elif not offset.isdigit() or offset[0] == '0':  # id不是正整数
        return HttpResponse(json.dumps(invalidParam), content_type="application/json")

    user = verify_session_id(cookie_id)

    # 访问数据库
    conn = sqlite3.connect('onlineDB.db')
    user_cursor = conn.cursor()
    user_cursor.execute('select * from data where id=?', (int(offset),))
    record = user_cursor.fetchall()  # 获取指定记录

    if not record or record[0][-1] != user:  # 记录不存在/不属于当前用户
        return HttpResponse(json.dumps(unknownRecord), content_type="application/json")

    if name:
        user_cursor.execute("update data set name = '%s' where id = %d" % (name, int(offset)))
    if timestamp:
        user_cursor.execute("update data set timestamp = '%s' where id = %d" % (timestamp, int(offset)))
    if content:
        user_cursor.execute("update data set content = '%s' where id = %d" % (content, int(offset)))

    conn.commit()

    user_cursor.close()
    conn.close()

    for key in request.POST:
        if key not in ('name', 'timestamp', 'content'):  # 请求正文中存在未知字段
            return HttpResponse(json.dumps(unknownField), content_type="application/json")

    data_info = {'record_id': '12'}
    data_info['record_id'] = int(offset)
    return HttpResponse(json.dumps(data_info), content_type="application/json")


@csrf_exempt
def get_record(request, offset):  # 获取记录
    # 异常处理
    cookie_id = request.COOKIES.get('session_id')
    if not cookie_id:  # 没有Cookies，尚未登录
        return HttpResponse(json.dumps(requireLogin), content_type="application/json")

    user = verify_session_id(cookie_id)
    # 访问数据库
    conn = sqlite3.connect('onlineDB.db')
    user_cursor = conn.cursor()
    user_cursor.execute('select * from data where id=?', (int(offset),))
    record = user_cursor.fetchall()  # 获取指定记录

    if not record or record[0][-1] != user:  # 记录不存在/不属于当前用户
        return HttpResponse(json.dumps(unknownRecord), content_type="application/json")

    # 正常，返回当前记录信息
    print(record)
    data_info = {'record_id': '12'}
    data_info['record_id'] = int(offset)
    data_info['name'] = record[0][0]
    data_info['content'] = record[0][1]
    front_ten_time = int(record[0][3][0:10])
    data_info['time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(front_ten_time)) + '.' + record[0][3][10:]
    return HttpResponse(json.dumps(data_info), content_type="application/json")


@csrf_exempt
def query(request):  # 查找记录
    # 异常处理
    cookie_id = request.COOKIES.get('session_id')
    if not cookie_id:  # 没有Cookies，尚未登录
        return HttpResponse(json.dumps(requireLogin), content_type="application/json")

    name = request.GET.get('name')
    if not name:  # URL参数'name'不存在或者为空
        return HttpResponse(json.dumps(illegalName), content_type="application/json")
    elif not name.strip():
        return HttpResponse(json.dumps(illegalName), content_type="application/json")

    # 访问数据库
    user = verify_session_id(cookie_id)
    conn = sqlite3.connect('onlineDB.db')
    user_cursor = conn.cursor()
    user_cursor.execute('select * from data where name=? and user=?', (name, user))
    record = user_cursor.fetchall()  # 获取指定记录

    return_list = []
    for item in record:
        data_info = {}
        data_info['record_id'] = int(item[2])
        data_info['name'] = item[0]
        data_info['content'] = item[1]
        front_ten_time = int(item[3][0:10])
        data_info['time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(front_ten_time)) + '.' + item[3][10:]
        return_list.append(data_info)

    data = {'list': []}
    data['list'] = return_list
    return HttpResponse(json.dumps(data, sort_keys=True, indent=4,
                                   separators=(',', ':')), content_type="application/json")
