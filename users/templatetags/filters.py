from django.template import Library

#实例化Library类用来注册过滤器
register = Library()
#注册方法一：register.filter('name',过滤器函数名)
#注册方法二：装饰器 @register.filter

@register.filter
def order_status(status):
    '''返回订单状态对应的字符串'''
    status_dict = {
        1: "待支付",
        2: "待发货",
        3: "待收货",
        4: "待评价",
        5: "已完成",
    }
    return status_dict[status]