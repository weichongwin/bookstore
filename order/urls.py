from django.conf.urls import url

from .views import *

urlpatterns = [
    url(r'^place/$',order_place,name='place'),
    url(r'^commit/$',order_commit,name='commit'),
    url(r'^pay/$', order_pay, name='pay'),
    url(r'^check_pay/$', check_pay, name='check_pay'),
]