from django.conf.urls import url

from .views import *

urlpatterns = [
    url(r'^register/$',register,name='register'),
    url(r'login/$',login,name='login'),
    url(r'logout/$',logout,name='logout'),
    url(r'^center/$',center,name='center'),
    url(r'^address/$',address,name='address'),
    url(r'^order/(?P<page>\d+)/$',order,name='order'),
    url(r'^verifycode/$',verifycode,name='verifycode'),
    url(r'^active/(?P<token>.*)/$', register_active, name='active'), # 用户激活
]
