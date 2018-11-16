$(function () {
    $('#btnLogin').click(function () {
        var username = $("#username").val()
        var password = $("#pwd").val()
        var remember = $('input[name="remember"]').prop('checked')
        var csrfmiddlewaretoken = $('input[name="csrfmiddlewaretoken"]').val()
        var vc = $('input[name="vc"]').val()

        var params = {
            'username': username,
            'password': password,
            'remember': remember,
            'csrfmiddlewaretoken': csrfmiddlewaretoken,
            'vc': vc,
        };
        $.post('/user/login/', params, function (data) {
            // 用户名密码错误 {'res': 0}
            // 登录成功 {'res': 1}
            if (data.res == 1) {
                // 跳转页面
                location.href = data.redirect_url;
            } else if (data.res == 2) {
                alert("数据不完整");
            } else if (data.res == 0) {
                alert("用户名或者密码错误");
            } else if(data.res == 3){
                alert('验证码错误')
            }
        })
    })
})
