/**
 * Created by jishu_linjie on 9/24/15.
 */
var CLICK_COUPON_TIMES = 1;

$("#coupon_release").click(function () {
    //领取优惠券
    if (CLICK_COUPON_TIMES > 1) {
        // 第二次点击跳转到优惠券页面
        location.href = "pages/youhuiquan.html";
    }
    var uldom = $("#tpl_ul_show");
    $.each($(uldom).children(), function (i, v) {
        var tmpid = $(v).attr("cid");
        var data = {"template_id": tmpid};
        var d = $("#coupon_release");
        console.log("data :", data);
        Action_release(data, d);
    });
    CLICK_COUPON_TIMES += 1; // 再次点击
});

function Action_release(data, d) {
    var url = GLConfig.baseApiUrl + GLConfig.usercoupons;

    $.ajax({
        "url": url,
        "data": data,
        "success": callback,
        "type": "post",
        "csrfmiddlewaretoken": csrftoken,
        error: function (data) {
            console.log('debug profile:', data);
            if (data.status == 403) {
                drawToast('您还没有登陆哦!');
            }
        }
    });
    function callback(res) {

        if (res.res == "success") {
            drawToast("领取成功 赶紧去挑选商品吧 不要过期哦！");
            //等待3秒跳转到优惠券页面
        }
        if (res.res == "already") {
            drawToast("您已经领取优惠券啦 赶紧去挑选商品吧 不要过期哦！");
        }
        if (res.res == "no_type") {
            drawToast("优惠券类型不正确呢！");
        }
        if (res.res == "not_release") {
            drawToast("还没有开放该优惠券哦 敬请期待！");
        }
        if (res.res == "cu_not_fund") {
            drawToast("用户未找到！尝试重新登陆");
        }
        if (res.res == "limit") {
            drawToast("超过领取限制哦~");
        }
    }
}

function Set_coupon_tpls() {
    var tpls_url = GLConfig.baseApiUrl + GLConfig.coupon_tpls;
    $.ajax({
        "url": tpls_url,
        "data": {},
        "success": callback,
        "type": "get",
        "csrfmiddlewaretoken": csrftoken
    });
    function callback(res) {
        console.log("tpls:", res);
        $.each(res, function (i, v) {
            var tplhml = create_tpl_show(v);
            $("#tpl_ul_show").append(tplhml);
        });
        // 调用轮播
        var autoplay = false;
        if (res.length > 1) {
            autoplay = true; //优惠券张数大于1的时候显示轮播
        }
        else if (res.length <= 0) {
            $(".glist_cou").remove();//没有优惠券的时候删除dom
        }
        CouponTemplateShow($(".glist_cou"), 500, 3000, autoplay);
    }

    function create_tpl_show(obj) {
        var copl = $("#coupon_tpl").html();
        return hereDoc(copl).template(obj)
    }
}

function CouponTemplateShow(dom, speed, delay, autoplay) {
    console.log("dom:", dom);
    $(dom).unslider({
        autoplay: autoplay,
        speed: speed,
        delay: delay,
        keys: false,
        arrows: false,
        nav: false
    });
}