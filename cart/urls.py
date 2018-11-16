from django.conf.urls import url
from .views import *

urlpatterns = [
    url(r'^add/$', cart_add, name='add'),  # 添加购物车数据
    url(r'^count/$',cart_count, name='count'),  # 获取用户购物车中商品的数量
    url(r'^$',cart_show,name='show'),
    url(r'^del/$',cart_del,name='delete'),
    url(r'^update/$',cart_update,name='update'),
]