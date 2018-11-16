$(function () {
    // 计算总价
    function update_total_price() {
        total_count = 0
        total_price = 0
        $('.cart_list_td').find(':checked').parents('ul').each(function () {
                // 计算商品的小计
                res_dict = update_books_price($(this))

                total_count += res_dict.books_count
                total_price += res_dict.books_amount
            })
        $('.settlements').find('em').text(total_price.toFixed(2))
        $('.settlements').find('b').text(total_count)
    }

    // 更新页面上购物车商品的总数
    function update_cart_count() {
            $.get('/cart/count/', function (data) {
                $('.total_count').children('em').text(data.res)
            })
            $.get('/cart/count/', function (data) {
                // {'res':商品的总数}
                $('#show_count').html(data.res)
            })
        }

    //接收一个ul元素,来设置它的小计,返回一个包含书籍数量和小计的字典
    function update_books_price(books_ul) {
            // 获取每一个商品的价格和数量
                books_price = books_ul.children('.col05').text()
                books_count = books_ul.find('.num_show').val()

                // 计算商品的小计
                books_price = parseFloat(books_price)
                books_count = parseInt(books_count)
                books_amount = books_price * books_count

                // 设置商品的小计
                books_ul.children('.col07').text(books_amount.toFixed(2) + '元')

                return {
                	'books_count': books_count,
                	'books_amount': books_amount
                }
        }

    //添加删除标签的点击事件
    $('.cart_list_td').children('.col08').children('a').click(function () {
            // 获取删除的商品的id
        books_ul = $(this).parents('ul');
        books_id = books_ul.find('.num_show').attr('books_id');
        csrf = $('input[name="csrfmiddlewaretoken"]').val();
        params = {
            "books_id": books_id,
            "csrfmiddlewaretoken": csrf
        };
        // 发起ajax请求，访问/cart/del/
        $.post('/cart/del/', params, function (data) {
            if (data.res == 3){
                // 删除成功
                // 移除商品对应的ul元素
                books_ul.remove(); // books.empty()
                // 判断商品对应的checkbox是否选中
                is_checked = books_ul.find(':checkbox').prop('checked');
                if (is_checked){
                    update_total_price()
                }
                // 更新页面购物车商品总数
                update_cart_count()
            }
        })
    });

    //封装更新操作，设置了同步，即使阻塞了其他操作也在所不惜
    error_update = false
    function update_remote_cart_info(books_id, books_count) {
        csrf = $('input[name="csrfmiddlewaretoken"]').val()
        params = {
            'books_id': books_id,
            'books_count': books_count,
            'csrfmiddlewaretoken': csrf
        }
        // 设置同步
        $.ajaxSettings.async = false
        // 发起请求，访问/cart/update/
        $.post('/cart/update/', params, function (data) {
            if (data.res == 5){
                // alert('更新成功')
                error_update = false
            }
            else {
                error_update = true
                alert(data.errmsg)
            }
        })
        // 设置异步
        $.ajaxSettings.async = true
    }

    // 商品增加
    $('.add').click(function () {
        // 获取商品的数量和id
        books_count = $(this).next().val();
        books_id = $(this).next().attr('books_id');
        // 加1
        books_count = parseInt(books_count) + 1;
        //更新redis购物车信息
        update_remote_cart_info(books_id, books_count);
        if (error_update == false){
            //更新成功，重新设置值
            $(this).next().val(books_count);
            is_checked = $(this).parents('ul').find(':checkbox').prop('checked')
            if (is_checked){
                // 更新商品的总数目，总价格和小计
                update_total_price()
            }
            else{
                // 更新商品的小计
                update_books_price($(this).parents('ul'))
            }
            update_cart_count()
        }
    });

    // 商品减少
    $('.minus').click(function () {
        // 获取商品的数量和id
        books_count = $(this).prev().val();
        books_id = $(this).prev().attr('books_id')
        books_count = parseInt(books_count) - 1;
        if (books_count == 0){
            books_count = 1
        }
        update_remote_cart_info(books_id, books_count)
        // 重新设置值
        if(error_update==false){
            $(this).prev().val(books_count);
            // 获取商品对应的checkbox的选中状态
            is_checked = $(this).parents('ul').find(':checkbox').prop('checked')
            if (is_checked){
                // 更新商品的总数目，总价格和小计
                update_total_price()
            }
            else{
                // 更新商品的小计
                update_books_price($(this).parents('ul'))
            }
            update_cart_count()
        }
    });

    //记录鼠标选中输入框时的商品数量，以便于鼠标离开时回滚数据
    pre_books_count = 0
    $('.num_show').focus(function () {
        pre_books_count = $(this).val()
    })

    // 手动输入
    $('.num_show').blur(function () {
        // 获取商品的数量和id
        books_count = $(this).val();
        books_id = $(this).attr('books_id')
        // 数据校验
        if (isNaN(books_count) || books_count.trim().length == 0 || parseInt(books_count) <= 0 ){
            // 设置回输入之前的值
            $(this).val(pre_books_count)
            return
        }
        books_count = parseInt(books_count)
        update_remote_cart_info(books_id, books_count)
        if(error_update==false){
            $(this).val(books_count);
            is_checked = $(this).parents('ul').find(':checkbox').prop('checked')
            if (is_checked){
                // 更新商品的总数目，总价格和小计
                update_total_price()
            }
            else{
                // 更新商品的小计
                update_books_price($(this).parents('ul'))
            }
            // 更新页面购物车商品总数
            update_cart_count()
        }else {
            $(this).val(pre_books_count)
        }

        // 计算总价
        update_total_price()
    })

    //改变全选按钮时状态同步给所有其他按钮
    $('.settlements').find(':checkbox').change(function () {
            // 获取全选checkbox的选中状态
        is_checked = $(this).prop('checked')
        // 遍历所有商品对应的checkbox,设置checked属性和全选checkbox一致
        $('.cart_list_td').find(':checkbox').each(function () {
            $(this).prop('checked', is_checked)
        })
        // 更新商品的信息
        update_total_price()
    })

    // 商品对应的checkbox状态发生改变时，全选checkbox的改变
    $('.cart_list_td').find(':checkbox').change(function () {
            // 获取所有商品对应的checkbox的数目
            all_len = $('.cart_list_td').find(':checkbox').length
            // 获取所有被选中商品的checkbox的数目
            checked_len  = $('.cart_list_td').find(':checked').length
            if (checked_len < all_len){
                $('.settlements').find(':checkbox').prop('checked', false)
            }
            else {
                 $('.settlements').find(':checkbox').prop('checked', true)
            }
            // 更新商品的信息
            update_total_price()
        })
});