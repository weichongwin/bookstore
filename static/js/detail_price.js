$(function () {
    update_total_price();
    // 计算总价
    function update_total_price() {
        // 获取商品的价格和数量
        books_price = $('.show_pirze').children('em').text();
        books_count = $('.num_show').val();
        // 计算商品的总价
        books_price = parseFloat(books_price);
        books_count = parseInt(books_count);
        total_price = books_price * books_count;
        // 设置商品总价
        $('.total').children('em').text(total_price.toFixed(2) + '元')
    }

    // 商品增加
    $('.add').click(function () {
        // 获取商品的数量
        books_count = $('.num_show').val();
        // 加1
        books_count = parseInt(books_count) + 1;
        // 重新设置值
        $('.num_show').val(books_count);
        // 计算总价
        update_total_price()
    });

    // 商品减少
    $('.minus').click(function () {
        // 获取商品的数量
        books_count = $('.num_show').val();
        // 加1
        books_count = parseInt(books_count) - 1;
        if (books_count == 0){
            books_count = 1
        }
        // 重新设置值
        $('.num_show').val(books_count);
        // 计算总价
        update_total_price()
    });

    // 手动输入
    $('.num_show').blur(function () {
        // 获取商品的数量
        books_count = $(this).val();
        // 数据校验
        if (isNaN(books_count) || books_count.trim().length == 0 || parseInt(books_count) <= 0 ){
            books_count = 1
        }
        // 重新设置值
        $(this).val(parseInt(books_count));
        // 计算总价
        update_total_price()
    })
});