$(function () {
    // 获取评论
    $.ajax({
        url: '/comment/' + $('#comment-input').data('bookid'),
        success: function (res) {
            if (res.code == 200) {
                var data = res.data;
                console.log(data);
                var div_head = '<div>';
                var div_tail = '</div>';
                var dom_element = ''
                for(i = 0; i < data.length; i++) {
                    var head = '<div>';
                    var tail = '</div>';
                    var temp = head  + '<span style="color: #0f81cc">' +'点评：'+ data[i].content + '</span>'+'<br>' +'<span>'+'该评论来自编号' + data[i].user_id +'的用户：'+ '</span>' +'<hr>' + tail;
                    dom_element += temp;
                }
                dom_element = div_head + dom_element + div_tail;
                $('#book_comment').append(dom_element);
            }
        }
    })

    $('#detail').click(function () {
        $(this).addClass('active');
        $('#comment').removeClass('active');
        $('#book_comment').hide();
        $('#book_detail').show();
    })
    $('#comment').click(function () {
        $(this).addClass('active');
        $('#detail').removeClass('active');
        $('#book_comment').show();
        $('#book_detail').hide();
    })
    $('#write-comment').click(function () {
        $('#comment-input').show();
    })
    $('#submit-comment').click(function () {
        var book_id = $('#comment-input').data('bookid');
        var user_id = $('#comment-input').data('userid');
        var content = $('#comment-input input').val();
        var data = {
            book_id: book_id,
            user_id: user_id,
            content: content,
        }
        console.log('content: ', content);
        $.ajax({
            type: 'POST',
            url: '/comment/' + book_id + '/',
            data: JSON.stringify(data),
            success: function (res) {
                if (res.code === 200) {
                    // console.log('res: ', res)
                    alert(res.msg)
                    $('#comment-input').hide();
                }
            }
        })
    })
})