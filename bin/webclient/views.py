from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json
import sqlite3

# 错误提示信息汇总
existUser = {'error': 'user exists'}  # 注册输入用户已存在
invalidParam = {'error': 'invalid parameters'}  # 参数为空或者非法
typePOST = {'error': 'require POST'}  # 应为POST请求

# 各接口对应网页汇总
logon_page = '''<form action="/logon" method="post">
Username:<input type="text" name="username" value="%s"/></br>
Password:<input type="password" name="password" value="%s"/></br>
<input type="submit" value="Submit"/>
</form>
'''


# 后台处理辅助函数
def judge_user_exist(user_name, pw):  # 判断注册输入用户是否已存在
    conn = sqlite3.connect('onlineDB.db')
    user_cursor = conn.cursor()
    # user_cursor.execute('create table if not exists user (username varchar(32) primary key, password varchar(32))')
    user_cursor.execute('select * from user where username=?', (user_name,))
    # print(user_name)  # for test only
    user = user_cursor.fetchall()
    # print(user)  # for test only

    # 不存在时存储当前用户
    if not user:
        # order = 'insert into user (username, password) values (\'' + user_name + '\', \'' + pw + '\')'
        conn = sqlite3.connect('onlineDB.db')
        user_cursor = conn.cursor()
        user_cursor.execute("insert into user (username, password) values ('%s','%s')" % (user_name, pw))

    user_cursor.close()
    conn.commit()
    conn.close()
    if user:
        return True
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

