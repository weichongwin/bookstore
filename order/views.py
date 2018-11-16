import os
import time

from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django_redis import get_redis_connection
from django.db import transaction

from books.models import Books
from utils.decorators import login_required
from users.models import Address, Passport
from .models import OrderInfo,OrderGoods
from datetime import datetime
from alipay import AliPay
from django.conf import settings
# Create your views here.

@login_required
def order_place(request):
    '''提交订单界面'''
    #接受POST传的商品id列表
    books_ids = request.POST.getlist('books_ids')
    #检验提交商品id是否为空
    if not all(books_ids):
        return redirect(reverse('cart:show'))
    #通过session的用户id获取收货地址
    passport_id = request.session.get('passport_id')
    addr = Address.objects.get_default_address(passport_id=passport_id)
    #创建储存用户要购买的商品对象的集合
    books_li = []
    #商品的总数和总金额
    total_count = 0
    total_price = 0
    #链接redis，获取购物车订单id
    conn = get_redis_connection('default')
    cart_key = 'cart_%d'%passport_id
    for id in books_ids:
        books = Books.objects.get_books_by_id(books_id=id)
        #从redis中获取商品数量
        count = conn.hget(cart_key,id)
        books.count = count
        #计算商品小计
        amount = int(count)*books.price
        books.amount = amount
        books_li.append(books)
        total_count += int(count)
        total_price += books.amount
    #运费和实付款
    transit_price = 10
    total_pay = total_price + transit_price
    #将商品id列表转化为字符串，用来作为提交订单超链接的一个属性，以便ajax获取
    books_ids = ','.join(books_ids)
    context = {
        'addr':addr,
        'books_li':books_li,
        'total_count':total_count,
        'total_price':total_price,
        'transit_price':transit_price,
        'total_pay':total_pay,
        'books_ids':books_ids,
    }
    return render(request,'order/place_order.html',context)

@transaction.atomic
def order_commit(request):
    '''对提交订单界面传递的信息进行处理，
    前端传递数据：地址 支付方式 购买的商品id，
    向订单表和订单商品表中添加信息，更新商品的销量和库存属性；
    清除购物车对应信息'''

    #先判断是否登陆
    if not request.session.has_key('islogin'):
        return JsonResponse({'res':0,'errmsg':'用户未登录'})
    #接收数据
    addr_id = request.POST.get('addr_id')
    pay_method = request.POST.get('pay_method')
    books_ids = request.POST.get('books_ids')

    #数据校验
    if not all([addr_id,pay_method,books_ids]):
        return JsonResponse({'res':1,'errmsg':'数据不完整'})

    #获取地址
    try:
        addr = Address.objects.get(id=addr_id)
    except Exception as e:
        # 地址信息出错
        return JsonResponse({'res': 2, 'errmsg': '地址信息错误'})

    if int(pay_method) not in OrderInfo.PAY_METHODS_ENUM.values():
        return JsonResponse({'res':3,'errmsg':'不支持的支付方式'})

    passport_id = request.session.get('passport_id')
    #订单id：时间+用户id
    order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(passport_id)
    # 运费
    transit_price = 10
    # 订单商品总数和总金额
    total_count = 0
    total_price = 0

    #创建一个保存点
    sid = transaction.savepoint()
    try:

        #向订单信息表中添加记录
        order = OrderInfo.objects.create(
            order_id=order_id,
            passport_id=passport_id,
            addr_id=addr_id,
            total_count=total_count,
            total_price=total_price,
            transit_price=transit_price,
            pay_method=pay_method)
        #向订单商品表中添加订单商品的记录

        books_ids = books_ids.split(',')
        conn = get_redis_connection('default')
        cart_key = 'cart_%d'%passport_id

        for id in books_ids:
            books = Books.objects.get_books_by_id(books_id=id)
            if books is None:
                transaction.savepoint_rollback(sid)
                return JsonResponse({'res':4,'errmsg':'商品信息错误'})

            #获取用户购买的商品数目
            count = conn.hget(cart_key,id)

            #判断商品库存
            if int(count) >books.stock:
                transaction.savepoint_rollback(sid)
                return JsonResponse({'res':5,'errmsg':'商品库存不足'})

            #创建一条商品记录
            OrderGoods.objects.create(
                order_id=order_id,
                books_id=id,
                count=count,
                price=books.price)
            #增加商品销量，减少库存

            books.sales += int(count)
            books.stock -= int(count)
            books.save()
            # 累计计算商品的总数目和总额
            total_count += int(count)
            total_price += int(count) * books.price

        #更新订单的商品总数目和总金额
        order.total_count = total_count
        order.total_price = total_price
        order.save()
    except Exception as e:
        transaction.savepoint_rollback(sid)
        return JsonResponse({'res':7,'errmsg':'服务器错误'})

    #清除购物车对应记录
    conn.hdel(cart_key,*books_ids)
    #事务提交
    transaction.savepoint_commit(sid)
    return JsonResponse({'res':6})



'''订单支付'''
@login_required
def order_pay(request):
    #接收订单id
    passport_id = request.session.get('passport_id')
    passport = Passport.objects.get(id = passport_id)
    if not passport.is_active:
        return JsonResponse({'res':0,'errmsg':'请您先前往邮箱激活账户'})
    order_id = request.POST.get('order_id')
    if not order_id:
        return JsonResponse({'res':1,'errmsg':'订单不存在'})
    try:
        order = OrderInfo.objects.get(order_id=order_id,status=1,pay_method=3)
    except OrderInfo.DoesNotExist :
        return JsonResponse({'res':2,'errmsg':'订单信息出错'})
    # 创建用于进行支付宝支付的工具对象
    alipay = AliPay(
        appid=settings.ALIPAY_APPID,
        app_notify_url=None,
        app_private_key_path=os.path.join(settings.BASE_DIR,'order/app_private_key.pem'),
        alipay_public_key_path=os.path.join(settings.BASE_DIR,'order/alipay_public_key.pem'),
        sign_type='RSA2',
        debug=True
    )
    # 电脑网站支付，需要跳转到ALIPAY_URL? + order_string
    total_pay = order.total_price + order.transit_price
    order_string = alipay.api_alipay_trade_page_pay(
        out_trade_no=order_id,
        total_amount=str(total_pay), # Json传递，需要将浮点转换为字符串
        subject='阶梯书城-%s'%order_id,
        return_url=None,
        notify_url=None
    )

    pay_url = settings.ALIPAY_URL + '?' + order_string
    return JsonResponse({'res':3,'pay_url':pay_url})


'''获取用户支付的结果'''
@login_required
def check_pay(request):
    passport_id = request.session.get('passport_id')
    #接收订单id
    order_id = request.POST.get('order_id')
    if not  order_id:
        return JsonResponse({'res':1,'errmsg':'数据不存在'})

    try:
        order = OrderInfo.objects.get(order_id=order_id,passport_id=passport_id,pay_method=3)
    except OrderInfo.DoesNotExist:
        return JsonResponse({'res':2,'errmsg':'订单信息错误'})

    alipay = AliPay(
        appid=settings.ALIPAY_APPID,
        app_notify_url=None,
        app_private_key_path=os.path.join(settings.BASE_DIR,'order/app_private_key.pem'),
        alipay_public_key_path=os.path.join(settings.BASE_DIR,'order/alipay_public_key'),
        sign_type='RSA2',
        debug=True
    )

    # while True:
    #     print('#########################')
    #     # 进行支付结果查询
    #     result = alipay.api_alipay_trade_query(order_id)
    #     print(result,'%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
    #     code = result.get('code')
    #     print(code,'^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')
    #     if code == '10000' and result.get('trade_status') == 'TRADE_SUCCESS':
    #         # 用户支付成功
    #         # 改变订单支付状态
    #         order.status = 2  # 待发货
    #         # 填写支付宝交易号
    #         order.trade_id = result.get('trade_no')
    #         order.save()
    #         # 返回数据
    #         print('111111111')
    #         return JsonResponse({'res': 3, 'message': '支付成功'})
    #     elif code == '40004' or (code == '10000' and result.get('trade_status') == 'WAIT_BUYER_PAY'):
    #         # 支付订单还未生成，继续查询
    #         # 用户还未完成支付，继续查询
    #         time.sleep(5)
    #         print(22222222222222222)
    #         continue
    #     else:
    #         # 支付出错
    #         print(333333333333333333)
    #         return JsonResponse({'res': 4, 'errmsg': '支付出错'})

    while True:
        # 调用alipay工具查询支付结果
        response = alipay.api_alipay_trade_query(order_id)  # response是一个字典
        # 判断支付结果
        code = response.get("code")  # 支付宝接口调用成功或者错误的标志
        trade_status = response.get("trade_status")  # 用户支付的情况

        if code == "10000" and trade_status == "TRADE_SUCCESS":
            # 表示用户支付成功
            # 返回前端json，通知支付成功
            return JsonResponse({"code": 3})

        elif code == "40004" or (code == "10000" and trade_status == "WAIT_BUYER_PAY"):
            # 表示支付宝接口调用暂时失败，（支付宝的支付订单还未生成） 后者 等待用户支付
            # 继续查询
            print(code)
            print(trade_status)
            continue
        else:
            # 支付失败
            # 返回支付失败的通知
            return JsonResponse({"code": 4, "errmsg": "支付失败"})