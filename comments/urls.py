from django.conf.urls import url

from .views import comment

urlpatterns = [
    url(r'^(?P<books_id>\d+)/$',comment,name='comment')
]
