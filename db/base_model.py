from django.db import models

class BaseModel(models.Model):
    '''模型抽象基类'''
    is_delete = models.BooleanField(default=False,verbose_name='是否删除')
    creare_time = models.DateField(auto_now_add=True,verbose_name='创建时间')
    update_time = models.DateField(auto_now=True,verbose_name='更新时间')

    class Meta:
        abstract =True  #abstract 表示模型是抽象基类