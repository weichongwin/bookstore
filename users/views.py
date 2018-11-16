import random
import re
import io
import os
from django.conf import settings
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from PIL import Image,ImageDraw,ImageFont
from django.http import HttpResponse
from django_redis import get_redis_connection
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired

from books.models import Books
from .models import Passport,Address
from utils.decorators import login_required
from order.models import OrderInfo,OrderGoods
from bookstore.settings import BASE_DIR
from users.tasks import send_active_email

'''注册'''
def register(request):
    if request.method=='POST':
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        if not all([username, password, email]):
            return render(request, 'users/register.html', {'errmsg': '参数不能为空'})
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'users/register.html', {'errmsg': '邮箱不合法!'})
        try:
            passport = Passport.objects.add_one_passport(username=username, password=password, email=email)
        except:
            return render(request, 'users/register.html', {'errmsg': '用户名已存在！'})
        #生成激活的token itsdangetous
        serializer = Serializer(settings.SECRET_KEY,3600)
        token = serializer.dumps({'confirm':passport.id})
        token = token.decode()

        # 同步/给用户的邮箱发激活邮件
        send_mail('阶梯书城用户激活', '', settings.EMAIL_HOST_USER, [email], html_message='<a href="http://127.0.0.1:8000/user/active/%s/">http://127.0.0.1:8000/user/active/</a>' % token)
        #异步发送激活邮件
        # send_active_email.delay(token,username,email)

        request.session['islogin'] = True
        request.session['username'] = username
        request.session['passport_id'] = passport.id
        return redirect(reverse('books:index'))
    return render(request,'users/register.html',)

'''显示登录页面'''
def login(request):
    if request.COOKIES.get("username"):
        username = request.COOKIES.get("username")
        checked = 'checked'
    else:
        username = ''
        checked = ''
    context = {
        'username': username,
        'checked': checked,
    }
    if request.method=='POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        vc = request.POST.get('vc')
        code = request.session.get('verifycode')
        if not all([username,password,vc]) :
            return JsonResponse({'res':2})
        if vc.upper() != code.upper():
            return JsonResponse({'res':3})
        #情况二：账号密码正确，设置session和cookie后，响应传递2个数据：res=1;
        #      redirect_url = 主页路由，给ajax来跳转到主页
        passport = Passport.objects.get_one_passport(username=username,password=password)
        if passport:
            redirect_url =reverse('books:index')
            jres = JsonResponse({'res':1,'redirect_url':redirect_url})

            if remember == 'true':
                jres.set_cookie('username',username,max_age=7*24*3600)
            else:
                jres.delete_cookie('username')

            #记住h用户的登录状态
            request.session['islogin'] = True
            request.session['username'] = username
            request.session['passport_id'] = passport.id
            return jres
        #情况三：账号密码错误，响应返回数据：res=0
        else:
            return JsonResponse({'res':0})
    return render(request, 'users/login.html', context)


'''退出登录，清空session'''
def logout(request):
    request.session.flush()
    return redirect(reverse('books:index'))

'''用户中心'''
@login_required
def center(request):

    passport_id = request.session.get('passport_id')
    addr = Address.objects.get_default_address(passport_id=passport_id)

    # 获取用户的最近浏览信息
    con = get_redis_connection('default')
    key = 'history_%d' % passport_id
    # 取出用户最近浏览的5个商品的id
    history_li = con.lrange(key, 0, 4)
    # 查询数据库,获取用户最近浏览的商品信息
    books_li = []
    for id in history_li:
        books = Books.objects.get_books_by_id(books_id=id)
        books_li.append(books)
    context = {
        'addr':addr,
        'books_li':books_li
    }
    return render(request,'users/user_center_info.html',context)


'''用户地址'''
@login_required
def address(request):
    passport_id = request.session.get('passport_id')
    if request.method == 'POST':
        '''添加收货地址'''
        recipient_name = request.POST.get('username')
        recipient_addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        recipient_phone = request.POST.get('phone')
        if not all([recipient_addr,recipient_name,recipient_phone,zip_code]):
            return render(request,'users/user_center_site.html',{'errmsg':'参数不能为空'})
        Address.objects.add_one_address(
            passport_id=passport_id,
            recipient_name=recipient_name,
            recipient_addr=recipient_addr,
            zip_code=zip_code,
            recipient_phone=recipient_phone
        )
        return redirect(reverse('user:address'))
    addr = Address.objects.get_default_address(passport_id=passport_id)
    return render(request,'users/user_center_site.html',{'addr':addr,'page':'address'})

'''用户中心订单页'''
@login_required
def order(request,page):
    passport_id = request.session.get('passport_id')
    #查询用户所有订单，返回订单列表
    order_li = OrderInfo.objects.filter(passport_id=passport_id).order_by('-order_id')

    #遍历获取订单的商品信息
    for order in order_li:
        #根据订单id获取所有订单商品列表
        order_id = order.order_id
        order_books_li = OrderGoods.objects.filter(order_id=order_id)

        #计算商品小计amount,给订单商品对象动态增加amount属性
        for order_books in order_books_li:
            count = order_books.count
            price = order_books.price
            order_books.amount = count * price

        #给order订单对象动态添加一个属性———订单商品列表order_books_li
        order.order_books_li = order_books_li

    paginator = Paginator(order_li,3) #每页显示3个订单
    num_pages = paginator.num_pages  #最大页数
    #判断page，默认为1
    if not page or page == '' or int(page) > num_pages:
        page = 1
    else:
        page = int(page)
    #获取page页面订单列表
    order_li = paginator.page(page)

    #根据当前page,控制页面导航条范围pages
    if num_pages < 5:
        pages = range(1,num_pages+1)
    elif page <= 3 :
        pages = range(1,6)
    elif num_pages - page <= 2:
        pages = (num_pages -4 ,num_pages +1)
    else:
        pages = (page-2,page+3)

    context = {
        'order_li' : order_li,
        'pages' : pages,
    }

    return render(request,'users/user_center_order.html',context)

'''验证码'''
def verifycode(request):

    bgcolor = (random.randint(0,255),random.randint(0,255),random.randint(0,255))
    #创建画布
    image = Image.new('RGB',(100,50),color=bgcolor)
    #获取画布中的画笔对象
    draw = ImageDraw.Draw(image)

    font = ImageFont.truetype(os.path.join(BASE_DIR,'Ubuntu-RI.ttf'),25)
    code = ''
    str1 = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    for i in range(4):
        character = random.choice(str1)
        code += character
        filt = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        draw.text((10+i*20,random.randint(5,15)),character,fill=filt,font=font)

    del draw
    request.session['verifycode'] = code
    #创建缓冲区
    buffer = io.BytesIO()
    #将图片保存在内存中，文件类型为png
    image.save(buffer,'png')
    # 将内存中的图片数据返回给客户端，类型为图片png
    return HttpResponse(buffer.getvalue(),'image/png')

'''用户账户激活'''
def register_active(request, token):
    serializer = Serializer(settings.SECRET_KEY, 3600)
    try:
        info = serializer.loads(token)
        passport_id = info['confirm']
        # 进行用户激活
        passport = Passport.objects.get(id=passport_id)
        passport.is_active = True
        passport.save()
        # 跳转的登录页
        return redirect(reverse('user:login'))
    except SignatureExpired:
        # 链接过期
        return HttpResponse('激活链接已过期')