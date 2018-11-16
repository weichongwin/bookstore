from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from django_redis import get_redis_connection
import logging

from .models import Books
from .enums import *

logger = logging.getLogger('django.request')


'''显示首页'''
# @cache_page(60*10)  #缓存首页
def index(request):

    #当我们访问首页的时候，在log/debug.log中有日志信息
    logger.info(request.body)

    # 查询每个种类的3个新品信息和4个销量最好的商品信息
    python_new = Books.objects.get_books_by_type(PYTHON, limit=3, sort='new')
    python_hot = Books.objects.get_books_by_type(PYTHON, limit=4, sort='hot')
    javascript_new = Books.objects.get_books_by_type(JAVASCRIPT, limit=3, sort='new')
    javascript_hot = Books.objects.get_books_by_type(JAVASCRIPT, limit=4, sort='hot')
    algorithms_new = Books.objects.get_books_by_type(ALGORITHMS, 3, sort='new')
    algorithms_hot = Books.objects.get_books_by_type(ALGORITHMS, 4, sort='hot')
    machinelearning_new = Books.objects.get_books_by_type(MACHINELEARNING, 3, sort='new')
    machinelearning_hot = Books.objects.get_books_by_type(MACHINELEARNING, 4, sort='hot')
    operatingsystem_new = Books.objects.get_books_by_type(OPERATINGSYSTEM, 3, sort='new')
    operatingsystem_hot = Books.objects.get_books_by_type(OPERATINGSYSTEM, 4, sort='hot')
    database_new = Books.objects.get_books_by_type(DATABASE, 3, sort='new')
    database_hot = Books.objects.get_books_by_type(DATABASE, 4, sort='hot')
    # 定义模板上下文
    context = {
        'python_new': python_new,
        'python_hot': python_hot,
        'javascript_new': javascript_new,
        'javascript_hot': javascript_hot,
        'algorithms_new': algorithms_new,
        'algorithms_hot': algorithms_hot,
        'machinelearning_new': machinelearning_new,
        'machinelearning_hot': machinelearning_hot,
        'operatingsystem_new': operatingsystem_new,
        'operatingsystem_hot': operatingsystem_hot,
        'database_new': database_new,
        'database_hot': database_hot,
    }
    # 使用模板
    return render(request, 'books/index.html', context)

'''商品详情'''
def detail(request,books_id):

    books =Books.objects.get_books_by_id(books_id=books_id)
    if not books:
        return redirect(reverse('books:index'))
    #新品推荐
    books_li = Books.objects.get_books_by_type(type_id=books.type_id,limit=2,sort='new')

    # 用户登录之后，才记录浏览记录
    # 每个用户浏览记录对应redis中的一条信息 格式:'history_用户id':[10,9,2,3,4]
    # [9, 10, 2, 3, 4]
    if request.session.has_key('islogin'):
        # 用户已登录，记录浏览记录
        con = get_redis_connection('default')
        key = 'history_%d' % request.session.get('passport_id')
        # 先从redis列表中移除books.id
        con.lrem(key, 0, books.id)
        con.lpush(key, books.id)
        # 保存用户最近浏览的5个商品
        con.ltrim(key, 0, 4)

    '''当前商品类型'''
    type_title = BOOKS_TYPE[books.type_id]
    return render(request,'books/detail.html',{'books':books,'books_li':books_li,'type_title':type_title})

def list(request,type_id,page):

    '''商品列表界面'''
    sort = request.GET.get('sort','default')
    #判断type——id是否合法
    if int(type_id) not in BOOKS_TYPE.keys():
        return redirect(reverse('books:index'))
    books_li =Books.objects.get_books_by_type(type_id=type_id,sort=sort)
    #实例分页，设置每页书籍数量:3
    paginator = Paginator(books_li,3)
    #.num_pages属性获取总页数
    num_pages = paginator.num_pages
    #判断传入参数page
    if page=='' or int(page) > num_pages or int(page) < 1:
        page=1
    else:
        page = int(page)

    #返回一个page类实例对象，包含一页所有书籍的可迭代对象
    books_li =paginator.page(page)
    ''' 根据当前page,控制页面导航条范围pages
        1.总页数<5, 显示所有页码
        2.当前页是前3页，显示1-5页
        3.当前页是后3页，显示后5页 10 9 8 7
        4.其他情况，显示当前页前2页，后2页，当前页'''
    if num_pages < 5:
        pages = range(1,num_pages)
    elif page < 4:
        pages = range(1,6)
    elif num_pages - page <=2:
        pages = range(num_pages-4,num_pages+1)
    else:
        pages = range(page-2,page+3)
    #新品推荐
    book_new = Books.objects.get_books_by_type(type_id=type_id,limit=2,sort='new')
    #设置上下文
    type_title = BOOKS_TYPE[int(type_id)]
    context = {
        'books_li':books_li,
        'book_new':book_new,
        'type_id':type_id,
        'sort':sort,
        'type_title':type_title,
        'pages':pages
    }
    return render(request,'books/list.html',context)