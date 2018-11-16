from django.shortcuts import render
from django.http import JsonResponse
from django_redis import get_redis_connection

from books.models import Books
from utils.decorators import login_required


@login_required
def cart_add(request):
    books_id = request.POST.get('books_id')
    books_count = request.POST.get('books_count')
    if not all([books_id,books_count]):
        return JsonResponse({'res':1,'errmsg':'数据不完整'})
    books = Books.objects.get_books_by_id(books_id=books_id)
    if not books:
        return JsonResponse({'res':2,'errmsg':'商品不存在'})

    try:
        books_count = int(books_count)
    except Exception as e:
        # 商品数目不合法
        return JsonResponse({'res': 3, 'errmsg': '商品数量必须为数字'})

    connect_redis = get_redis_connection('default')
    cart_key = 'cart_%d'%request.session.get('passport_id')
    res = connect_redis.hget(cart_key, books_id)
    if res is None:
        # 如果用户的购车中没有添加过该商品，则添加数据
        res = books_count
    else:
        # 如果用户的购车中已经添加过该商品，则累计商品数目
        res = int(res) + books_count

    # 判断商品的库存
    if res > books.stock:
        # 库存不足
        return JsonResponse({'res': 4, 'errmsg': '商品库存不足'})
    else:
        connect_redis.hset(cart_key, books_id, res)

    # 返回结果
    return JsonResponse({'res': 5,'errmsg':'成功加入购物车！'})

@login_required
def cart_count(request):
    '''获取用户购物车中商品的总数'''
    connetion = get_redis_connection('default')
    cart_key = 'cart_%d'%request.session.get('passport_id')
    res_list = connetion.hvals(cart_key)
    res = 0
    for i in res_list:
        res += int(i)
    return JsonResponse({'res':res})

@login_required
def cart_show(request):
    '''显示购物车页面'''
    passport_id = request.session.get('passport_id')
    connection = get_redis_connection('default')
    cart_key = 'cart_%d'%passport_id
    res_dict = connection.hgetall(cart_key)
    books_li = []
    total_count = 0
    total_price = 0
    for id,count in res_dict.items():
        books = Books.objects.get_books_by_id(books_id=id)
        books.count = count
        books.amount = int(count)*books.price
        books_li.append(books)
        total_count += int(count)
        total_price += int(count)*books.price

    context = {
        'books_li':books_li,
        'total_count':total_count,
        'total_price':total_price
    }
    return render(request,'cart/cart.html',context)


@login_required
def cart_del(request):
    '''删除购物车中额商品'''
    books_id = request.POST.get('books_id')
    if not books_id:
        return JsonResponse({'res':1,'errmsg':'数据不完整'})
    books = Books.objects.get_books_by_id(books_id)
    if not books:
        return JsonResponse({'res':2,'errmsg':'商品不存在'})
    connection = get_redis_connection('default')
    cart_key = 'cart_%d'%request.session.get('passport_id')
    connection.hdel(cart_key,books_id)
    return JsonResponse({'res':3})

@login_required
def cart_update(request):
    '''更新购物车商品数目'''
    # 接收数据
    books_id = request.POST.get('books_id')
    books_count = request.POST.get('books_count')
    # 数据的校验
    if not all([books_id, books_count]):
        return JsonResponse({'res': 1, 'errmsg': '数据不完整'})
    books = Books.objects.get_books_by_id(books_id=books_id)
    if books is None:
        return JsonResponse({'res': 2, 'errmsg': '商品不存在'})
    try:
        books_count = int(books_count)
    except Exception as e:
        return JsonResponse({'res': 3, 'errmsg': '商品数目必须为数字'})
    # 更新操作
    conn = get_redis_connection('default')
    cart_key = 'cart_%d' % request.session.get('passport_id')
    # 判断商品库存
    if books_count > books.stock:
        return JsonResponse({'res': 4, 'errmsg': '商品库存不足'})
    conn.hset(cart_key, books_id, books_count)
    return JsonResponse({'res': 5})