$(function () {
    $('#add_cart').click(function () {
        
        //获取商品id个数量
        var books_id = $(this).attr('books_id');
        var books_count = $('.num_show').val();
        var csrf = $('input[name="csrfmiddlewaretoken"]').val();
        var params = {
            'books_id':books_id,
            'books_count':books_count,
            'csrfmiddlewaretoken':csrf
        };
        $.post('/cart/add/',params,function (data) {
            if (data.res==5){
                var count = $('#show_count').html();
                var count = parseInt(count) + parseInt(books_count);
                $('#show_count').html(count);
                alert('成功加入购物车！')
            } else {
                // var count = $('#show_count').html();
                // alert(count)
                // var count = parseInt(count) + parseInt(books_count);
                // alert(count);
                alert(data.errmsg);
            }
        })
    })
});