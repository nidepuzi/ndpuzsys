# coding:utf-8

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, render
from django.core import serializers
from shopback.items.models import Product, ProductSku
from flashsale.dinghuo.models import orderdraft, OrderDetail, OrderList
from django.forms.models import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder
import json, datetime
from django.views.decorators.csrf import csrf_exempt
from flashsale.dinghuo import paramconfig as pcfg
from django.template import RequestContext
from django.core.paginator import Paginator, InvalidPage, EmptyPage, PageNotAnInteger
from flashsale.dinghuo import log_action, ADDITION, CHANGE


def orderadd(request):
    user = request.user
    orderDr = orderdraft.objects.all().filter(buyer_name=user)

    return render_to_response('dinghuo/orderadd.html', {"orderdraft": orderDr},
                              context_instance=RequestContext(request))


def searchProduct(request):
    response = HttpResponse()
    response['Content-Type'] = "text/javascript"
    ProductIDFrompage = request.GET.get("searchtext", "")
    productRestult = Product.objects.filter(outer_id__icontains=ProductIDFrompage)
    # data = serializers.serialize("json", productRestult)
    product_list = []
    for product in productRestult:
        product_dict = model_to_dict(product)
        product_dict['prod_skus'] = []

        guiges = product.prod_skus.all()
        for guige in guiges:
            sku_dict = model_to_dict(guige)
            product_dict['prod_skus'].append(sku_dict)

        product_list.append(product_dict)

    data = json.dumps(product_list, cls=DjangoJSONEncoder)
    return HttpResponse(data)


@csrf_exempt
def initdraft(request):
    user = request.user
    if request.method == "POST":

        post = request.POST

        product_counter = int(post["product_counter"])
        for i in range(1, product_counter + 1):
            product_id_index = "product_id_" + str(i)
            product_id = post[product_id_index]
            guiges = ProductSku.objects.filter(product_id=product_id)
            for guige in guiges:
                guigequantityindex = product_id + "_tb_quantity_" + str(guige.id)
                guigequantity = post[guigequantityindex]
                mairujiageindex = product_id + "_tb_cost_" + str(guige.id)
                mairujiage = post[mairujiageindex]
                mairujiage = float(mairujiage)
                if guigequantity and mairujiage and mairujiage != 0 and guigequantity != "0":
                    guigequantity = int(guigequantity)
                    mairujiage = float(mairujiage)
                    try:
                        p1 = Product.objects.get(id=product_id)
                    except Exception as e:
                        print e
                    draftquery = orderdraft.objects.filter(buyer_name=user, product_id=product_id,
                                                           chichu_id=guige.id)
                    if draftquery:
                        draftquery[0].buy_quantity = draftquery[0].buy_quantity + guigequantity
                        draftquery[0].save()
                    else:
                        shijian = datetime.datetime.now()
                        tdraft = orderdraft(buyer_name=user, product_id=product_id, outer_id=p1.outer_id,
                                            buy_quantity=guigequantity, product_name=p1.name, buy_unitprice=mairujiage,
                                            chichu_id=guige.id, product_chicun=guige.name, created=shijian)
                        tdraft.save()
                else:
                    guigequantity = 0
        return HttpResponseRedirect("/sale/dinghuo/dingdan/")
    elif request.method == "GET":
        response = HttpResponse()
        response['Content-Type'] = "text/javascript"
        tb_id = request.GET.get("tb_outer", "hello")
        tb_outer_id = request.GET.get("tb_outer_id", "")
        buy_quantity = request.GET.get("buy_quantity", "0")

        tb_sku_name = request.GET.get("tb_sku_name", "")
        buy_unitprice = request.GET.get("but_unit_price", "")
        try:
            productRestult = Product.objects.get(outer_id=tb_outer_id)
        except Exception as e:
            print e
        draftqueryset = orderdraft.objects.filter(product_id=tb_outer_id, product_chicun=tb_sku_name)
        if draftqueryset:
            draftqueryset[0].buy_quantity = draftqueryset[0].buy_quantity + int(buy_quantity)
            draftqueryset[0].save()
        else:
            try:
                shijian = datetime.datetime.now()
                oDraft = orderdraft(buyer_name=user, product_id=tb_outer_id, buy_quantity=int(buy_quantity),
                                    product_name=productRestult.name, buy_unitprice=float(buy_unitprice), chichu_id="1",
                                    product_chicun=tb_sku_name, created=shijian)

                oDraft.save()
            except Exception as e:
                print e
        orderDrAll = orderdraft.objects.all().filter(buyer_name=user)
        data = serializers.serialize("json", orderDrAll)
        return HttpResponse(data)


@csrf_exempt
def neworder(request):
    username = request.user
    orderDrAll = orderdraft.objects.all().filter(buyer_name=username)
    orderlist = None
    if request.method == 'POST':
        post = request.POST
        costofems = post['costofems']
        if costofems=="":
            costofems = 0
        else:
            costofems = int(costofems)
        shijian = datetime.datetime.now()
        receiver = post['consigneeName']
        supplierId = post['supplierId']
        storehouseId = post['storehouseId']
        express_company = post['express_company']
        express_no = post['express_no']
        businessDate = datetime.datetime.now()
        remarks = post['remarks']
        amount = calamount(username, costofems)
        orderlist = OrderList()
        orderlist.buyer_name = username
        orderlist.costofems = costofems
        orderlist.receiver = receiver
        orderlist.express_company = express_company
        orderlist.express_no = express_no
        orderlist.supplier_name = supplierId
        orderlist.created = businessDate
        orderlist.updated = businessDate
        orderlist.note = remarks
        orderlist.status = pcfg.SUBMITTING
        orderlist.order_amount = amount
        orderlist.save()

        drafts = orderdraft.objects.filter(buyer_name=username)
        for draft in drafts:
            total_price = draft.buy_quantity * draft.buy_unitprice
            orderdetail1 = OrderDetail()
            orderdetail1.orderlist_id = orderlist.id
            orderdetail1.product_id = draft.product_id
            orderdetail1.outer_id = draft.outer_id
            orderdetail1.product_name = draft.product_name
            orderdetail1.product_chicun = draft.product_chicun
            orderdetail1.chichu_id = draft.chichu_id
            orderdetail1.buy_quantity = draft.buy_quantity
            orderdetail1.total_price = total_price
            orderdetail1.buy_unitprice = draft.buy_unitprice
            orderdetail1.created = shijian
            orderdetail1.updated = shijian
            orderdetail1.save()
        drafts.delete()
        log_action(request.user.id, orderlist, CHANGE, u'新建订货单')
        return HttpResponseRedirect("/sale/dinghuo/detail/" + str(orderlist.id))

    return render_to_response('dinghuo/shengchengorder.html', {"orderdraft": orderDrAll},
                              context_instance=RequestContext(request))


def calamount(u, costofems):
    amount = 0;
    print costofems
    drafts = orderdraft.objects.all().filter(buyer_name=u)
    try:
        for draft in drafts:
            amount = amount + draft.buy_unitprice * draft.buy_quantity
        amount = amount + costofems
    except Exception as e:
        print e
    return amount


def CheckOrderExist(request):
    response = HttpResponse()
    response['Content-Type'] = "text/javascript"
    orderIDFrompage = request.GET.get("orderID", "")
    orderM = OrderList.objects.filter(orderlistID=orderIDFrompage)
    if orderM:
        result = """{"result":true}"""
    else:
        result = """{"result":false}"""
    return HttpResponse(result)


def delcaogao(request):
    username = request.user
    drafts = orderdraft.objects.filter(buyer_name=username)
    drafts.delete()
    return HttpResponse("")


def addpurchase(request):
    user = request.user
    ProductIDFrompage = "10802";
    productRestult = Product.objects.filter(outer_id__icontains=ProductIDFrompage)
    productguige = ProductSku.objects.all()
    orderDrAll = orderdraft.objects.all().filter(buyer_name=user)
    return render_to_response("dinghuo/addpurchasedetail.html",
                              {"productRestult": productRestult,
                               "productguige": productguige,
                               "drafts": orderDrAll},
                              context_instance=RequestContext(request))


def test(req):
    return render_to_response("dinghuo/testJsonto.html")


@csrf_exempt
def plusquantity(req):
    post = req.POST
    draftid = post["draftid"]
    draft = orderdraft.objects.get(id=draftid)
    draft.buy_quantity = draft.buy_quantity + 1
    draft.save()
    return HttpResponse("OK")


@csrf_exempt
def minusquantity(req):
    post = req.POST
    draftid = post["draftid"]
    draft = orderdraft.objects.get(id=draftid)
    draft.buy_quantity = draft.buy_quantity - 1
    draft.save()
    return HttpResponse("OK")


@csrf_exempt
def removedraft(req):
    post = req.POST
    draftid = post["draftid"]
    draft = orderdraft.objects.get(id=draftid)
    draft.delete()
    return HttpResponse("OK")


@csrf_exempt
def viewdetail(req, orderdetail_id):
    orderlist = OrderList.objects.get(id=orderdetail_id)
    orderdetail = OrderDetail.objects.filter(orderlist_id=orderdetail_id)
    paginator = Paginator(orderdetail, 7)
    page = req.GET.get('page')
    dict = {}
    for i in range(1, paginator.num_pages + 1):
        dict[i] = i
    try:
        orderdetail = paginator.page(page)
    except PageNotAnInteger:
        orderdetail = paginator.page(1)
    except EmptyPage:
        orderdetail = paginator.page(paginator.num_pages)
    return render_to_response("dinghuo/orderdetail.html", {"orderlist": orderlist,
                                                           "orderdetails": orderdetail,
                                                           "num_page": dict},
                              context_instance=RequestContext(req))


@csrf_exempt
def changestatus(req):
    post = req.POST
    orderid = post["orderid"]
    status_text = post["func"]
    orderlist = OrderList.objects.get(orderlistID=orderid)
    orderlist.status = status_text
    orderlist.save()
    state = True
    if status_text == "审核":
        state = True
    else:
        state = False
    log_action(req.user.id, orderlist, CHANGE, u'%s采购单' % (state and u'审核' or u'作废'))
    return HttpResponse("OK")
