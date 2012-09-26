import json
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.template.loader import render_to_string
from djangorestframework.serializer import Serializer
from djangorestframework.utils import as_tuple
from djangorestframework import status
from djangorestframework.response import Response
from djangorestframework.mixins import CreateModelMixin
from djangorestframework.views import ModelView,ListOrCreateModelView,ListModelView
from shopback.base.models import NORMAL
from shopback.items.models import Item,Product,ProductSku
from shopback.users.models import User
from shopback.items.tasks import updateUserItemsTask
from auth import apis


def update_user_items(request):

    content = request.REQUEST
    user_id = content.get('user_id') or request.user.get_profile().visitor_id

    update_nums = updateUserItemsTask(user_id)


    response = {'update_nums':update_nums}

    return HttpResponse(json.dumps(response),mimetype='application/json')



def update_user_item(request):

    content = request.REQUEST
    user_id = content.get('user_id')
    num_iid = content.get('num_iid')

    try:
        profile = User.objects.get(visitor_id=user_id)
    except User.DoesNotExist:
        return HttpResponse(json.dumps({'code':0,'error_reponse':'user_id is not correct'}))

    try:
        Item.objects.get(num_iid=None)
    except Item.DoesNotExist:
        try:
            response = apis.taobao_item_get(num_iid=num_iid,tb_user_id=profile.visitor_id)
            item_dict = response['item_get_response']['item']
            item = Item.save_item_through_dict(user_id,item_dict)

        except Exception,e:
            return HttpResponse(json.dumps({'code':0,'error_reponse':'update item fail.'}))

    item_dict = {'code':1,'reponse':Serializer().serialize(item)}
    return  HttpResponse(json.dumps(item_dict,cls=DjangoJSONEncoder))



class ProductListView(ListOrCreateModelView):
    """ docstring for ProductListView """
    queryset = None
    
    def get(self, request, *args, **kwargs):
        
        model = self.resource.model

        queryset = self.get_queryset() if self.get_queryset() is not None else model.objects.all()

        if hasattr(self, 'resource'):
            ordering = getattr(self.resource, 'ordering', None)
        else:
            ordering = None

        kwargs.update({'status':NORMAL})

        if ordering:
            args = as_tuple(ordering)
            queryset = queryset.order_by(*args)
        return queryset.filter(**kwargs)

    
    def post(self, request, *args, **kwargs):
        
        
        
        return None
    
    def get_queryset(self):
        return self.queryset
    

class ProductItemView(ListModelView):
    """ docstring for ProductListView """
    queryset = None
    
    def get(self, request, *args, **kwargs):
        
        model = self.resource.model

        queryset = self.get_queryset() if self.get_queryset() is not None else model.objects.all()

        if hasattr(self, 'resource'):
            ordering = getattr(self.resource, 'ordering', None)
        else:
            ordering = None

        if ordering:
            args = as_tuple(ordering)
            queryset = queryset.order_by(*args)
            
        item_dict = {}
        items = queryset.filter(**kwargs)
        item_dict['items'] =  Serializer().serialize(items)
        
        item_dict['layer_table'] = render_to_string('items/itemstable.html', { 'object':item_dict['items']})    
        
        return item_dict
    
    def get_queryset(self):
        return self.queryset


