/**
 *@author: imeron
 *@date: 2015-07-22 
 */
 
function parseTimeSM(start_time){
	//将时间差格式化成字符串[分:秒]
	var d1 = new Date(start_time);
	var d2 = new Date();
	var time_delta = parseInt((d2.getTime() - d1.getTime()) / 1000);
	var time_alias =  GLConfig.order_expired_in - time_delta;
	console.log('debug parse:',d1,time_delta,time_alias);
	if (time_alias < 0){
		 return '00:00';
	}
	var minute = parseInt(time_alias / 60);
	var second = parseInt(time_alias % 60);
	return (minute < 10 ?'0'+minute:minute.toString()+':') + (second < 10 ?'0'+second:second.toString())
	
}

function setOrderTimeInterval(){
	var has_period = false;
	$('.shengyu').each(function(index,e){
		var created_str  = $(e).attr('xl_created');
		console.log('debug attr:',created_str);
		var time_str = parseTimeSM(created_str);
		$(e).html('剩余时间：'+time_str);
		if (time_str != '00:00'){
			has_period = true
		}
	});
	//如果页面没有需要更新的计时任务则退出
	if (!has_period){return}
	setInterval(setOrderTimeInterval,1000);
}

function Create_order_dom(obj){
	//创建特卖订单DOM
	obj.created = obj.created.replace(/[TZ]/g,' ').replace(/-/g,'/')
	console.log('obj.created',obj.created);
	if (obj.status == 1){
		obj.btn_class   = 'shengyu';
		obj.btn_content = '剩余时间：'+parseTimeSM(obj.created);
	}else if(obj.status == 2){
		obj.btn_class   = 'btn-qianshou';
		obj.btn_content = '确认签收';
	}else{
		obj.btn_class   = '';
		obj.btn_content = '';
	}
	function Order_dom(){
	/*
	<li>
    <div class="top clear">
      <div class="xiadan">下单时间：{{ created }}</div>
      <div class="{{btn_class}}" xl_created="{{created}}">{{btn_content}}</div>
    </div>
    <a href="./dd-detail.html?id={{ id }}" class="info clear">
      <div class="left"><img src="{{ order_pic }}" /></div>
      <div class="right">
        <p>订单编号：<span class="caaaaaa orderno">{{ tid }}</span></p>
        <p>订单状态：<span class="caaaaaa">{{ status_display }}</span></p>
        <p>订单金额：<span class="cf353a0"><em>¥</em>{{ payment }}</span></p>
      </div>
    </a>
    </li>
    */};
  return hereDoc(Order_dom).template(obj)
}

function Set_orders(suffix){
	//请求URL
	var requestUrl = GLConfig.baseApiUrl + suffix;

	//请求成功回调函数
	var requestCallBack = function(data){
		if (typeof(data.count) != 'undifined' && data.count != null){
			$.each(data.results,
				function(index,order){
					var order_dom = Create_order_dom(order);
					$('.order_ul').append(order_dom);
				}
			);
		}
	};
	// 发送请求
	$.ajax({ 
		type:'get', 
		url:requestUrl, 
		data:{}, 
		dataType:'json', 
		success:requestCallBack 
	}); 
	
	//设置订单剩余时间更新
	setOrderTimeInterval();
}

function Create_order_top_dom(obj){
	//创建订单基本信息DOM
	function Top_dom(){
	/*
    <ul class="u1">
      <li><label class="c5f5f5e">订单状态：</label><span class="caaaaaa" id="status_display">{{ status_display }}</span></li>
      <li><label class="c5f5f5e">订单编号：</label><span class="caaaaaa">{{ tid }}</span></li>
      <li><label class="c5f5f5e">订单时间：</label><span class="caaaaaa">{{ created }}</span></li>
      <li><label class="c5f5f5e">订单金额：</label><span class="cf353a0"><em>¥</em>{{ payment }}</span></li>
    </ul>
    <a  class="btn-quxiao">取消订单</a>
	*/};
	return hereDoc(Top_dom).template(obj);
}

function Create_detail_dom(obj){
	//创建订单基本信息DOM
	function Detail_topdom(){
	/*
	   <div class="goods clear">
	      <div class="fl goods-img">
	        <img src="{{ pic_path }}">
	      </div> 
	      <div class="fr goods-info">
	        <p>{{ title }}</p>
	        <p>
	          <span class="size">尺码：{{ sku_name }}</span> 
	          <span class="count">数量：{{ num }}</span>
	        </p>
	        <p class="price">单价：<span class="gprice"><em>¥</em>{{ payment }}</span></p>
	      </div> 
	    </div> 
	*/};
	return hereDoc(Detail_topdom).template(obj);
}
 
function Create_detail_shouhuo_dom(obj){
	//创建订单收货信息DOM
	function Shouhuo_dom(){
	/*
    <div class="info">
      <p class="clear">
        <span class="label">收货人：</span>
        <span class="value">{{ receiver_name }}</span>
      </p>
      <p class="clear">
        <span class="label">手机号码：</span>
        <span class="value">{{ receiver_mobile }}</span>
      </p>
      <p class="clear">
        <span class="label">收货地址：</span>
        <span class="value">{{ receiver_state }} - {{ receiver_city }} - {{ receiver_district }} - {{ receiver_address }}</span>
      </p>  
    </div>
	*/};
	return hereDoc(Shouhuo_dom).template(obj);
}

function Create_detail_feiyong_dom(obj){
	//创建订单费用信息DOM
	function Feiyong_dom(){
	/*
    <div class="info">
      <p class="clear">
        <span class="label">商品总金额：</span>
        <span class="value"><em>¥</em> {{ total_fee }}</span>
      </p>
      <p class="clear">
        <span class="label">运费：</span>
        <span class="value"><em>¥</em> {{ post_fee }}</span>
      </p>
      <p class="clear">
        <span class="label">优惠金额：</span>
        <span class="value"><em>¥</em> -{{ discount_fee }}</span>
      </p> 
      <p class="clear">
        <span class="label">应付金额：</span>
        <span class="value total"><em>¥</em> {{ payment }}</span>
      </p>  
    </div>
	*/};
	return hereDoc(Feiyong_dom).template(obj);
}


function Set_order_detail(suffix){
	//请求URL
	var requestUrl = GLConfig.baseApiUrl + suffix;
	
	//请求成功回调函数
	var requestCallBack = function(data){
		if (typeof(data.id) != 'undifined' && data.id != null){
			//设置订单基本信息
			var top_dom = Create_order_top_dom(data);
			$('.basic .panel-top').append(top_dom);
			//设置订单收货信息
			var shouhuo_dom = Create_detail_shouhuo_dom(data);
			$('.shouhuo .panel-bottom').append(shouhuo_dom);
			//设置订单费用信息
			var feiyong_dom = Create_detail_feiyong_dom(data);
			$('.feiyong .panel-bottom').append(feiyong_dom);
			//设置订单商品明细
			$.each(data.orders,
				function(index,order){
					var detail_dom = Create_detail_dom(order);		
					$('.basic .panel-bottom').append(detail_dom);			
				}
			);

            Cancel_order(suffix);//页面加载完成  调用 取消订单功能
		}
	};
	// 发送请求
	$.ajax({ 
		type:'get', 
		url:requestUrl, 
		data:{}, 
		dataType:'json', 
		success:requestCallBack 
	}); 
}

function Cancel_order(suffix) {
    // 取消订单
    $(".btn-quxiao").click(function () {
        if ($("#status_display").html() == "交易关闭") {
            drawToast("交易已经取消！");
        }
        else {
            var cancel_bt = $(".btn-quxiao");
            //取消订单
            var arr = suffix.split('/'); //分割字符串获取订单id  /trades/78/orders/details.json
            var requestUrl = GLConfig.baseApiUrl + GLConfig.delete_detail_trade.template({"trade_id": arr[2]});
             ///rest/v1/trades/77  请求的地址
            if (cancel_bt.hasClass('loading')) {
                return;
            }
            cancel_bt.addClass('loading');
            function requestCallBack(res) {
                if (res['ok']) {
                    $("#status_display").html("交易关闭");
                    drawToast("交易已经取消！");
                    //删除取消退款的button
                    $(".btn-quxiao").remove();
                    //删除最下方购买button
                    $(".btn-buy").remove();
                }
                else{
                    drawToast("取消失败，请尝试刷新页面！");
                }
            }

            $.ajax({
                type: 'post',
                url: requestUrl,
                data: {'csrfmiddlewaretoken': csrftoken, '_method': 'DELETE'},//封装请求要求的request.data
                dataType: 'json',
                success: requestCallBack
            });
        }
    });
}



