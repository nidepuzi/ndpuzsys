import datetime
import json
from django.http import HttpResponse
from .models import PrintAsyncTaskModel
from shopapp.asynctask.tasks import AsyncCategoryTask, AsyncOrderTask, PrintAsyncTask, PrintAsyncTask2
from common.utils import parse_date

from rest_framework import generics
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework import permissions
from rest_framework.compat import OrderedDict
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer, BrowsableAPIRenderer
from rest_framework.views import APIView
from rest_framework import filters
from rest_framework import authentication
from . import serializers


class AsyncCategoryView(APIView):
    """ docstring for class AsyncCategoryView """
    serializer_class = serializers.PrintAsyncTaskModeSerializer
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)

    # print "start3333"
    def get(self, request, cids, *args, **kwargs):
        profile = request.user.get_profile()
        content = request.REQUEST
        seller_type = profile.type

        result = AsyncCategoryTask.delay(cids, profile.visitor_id, seller_type=seller_type)

        return Response({"task_id": result})

    post = get


class AsyncOrderView(APIView):
    """ docstring for class AsyncOrderView """
    serializer_class = serializers.PrintAsyncTaskModeSerializer
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)

    def get(self, request, start_dt, end_dt, *args, **kwargs):
        profile = request.user.get_profile()
        content = request.REQUEST

        start_dt = parse_date(start_dt)
        end_dt = parse_date(end_dt)

        result = AsyncOrderTask.delay(start_dt, end_dt, profile.visitor_id)
        return Response({"task_id": result})

    post = get


class AsyncInvoicePrintView(APIView):
    """ docstring for class AsyncPrintView """
    serializer_class = serializers.PrintAsyncTaskModeSerializer
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (TemplateHTMLRenderer, BrowsableAPIRenderer)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    template_name = "asynctask/async_print_commit.html"

    # print "start   AsyncInvoicePrintView"
    def get(self, request, *args, **kwargs):
        print " get  function"
        profile = request.user
        content = request.REQUEST

        params = {'trade_ids': content.get('trade_ids'),
                  'user_code': content.get('user_code')}
        task_model = PrintAsyncTaskModel.objects.create(
            task_type=PrintAsyncTaskModel.INVOICE,
            operator=profile.username,
            params=json.dumps(params))

        print_async_task = PrintAsyncTask.delay(task_model.pk)

        return Response({"task_id": print_async_task, "async_print_id": task_model.pk})

    post = get

class AsyncInvoice2PrintView(APIView):
    """ docstring for class AsyncPrintView """
    serializer_class = serializers.PrintAsyncTaskModeSerializer
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (TemplateHTMLRenderer, BrowsableAPIRenderer)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    template_name = "asynctask/async_print_commit.html"

    # print "start   AsyncInvoicePrintView"
    def get(self, request, *args, **kwargs):
        print " get  function"
        profile = request.user
        content = request.REQUEST

        params = {'trade_ids': content.get('trade_ids'),
                  'user_code': content.get('user_code')}
        task_model = PrintAsyncTaskModel.objects.create(
            task_type=PrintAsyncTaskModel.INVOICE,
            operator=profile.username,
            params=json.dumps(params))

        print_async_task = PrintAsyncTask2.delay(task_model.pk)

        return Response({"task_id": print_async_task, "async_print_id": task_model.pk})


class AsyncExpressPrintView(APIView):
    """ docstring for class AsyncPrintView """
    serializer_class = serializers.PrintAsyncTaskModeSerializer
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (TemplateHTMLRenderer, BrowsableAPIRenderer)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication,)
    template_name = "asynctask/async_print_commit.html"

    def get(self, request, *args, **kwargs):
        profile = request.user
        content = request.REQUEST

        params = {'trade_ids': content.get('trade_ids'),
                  'user_code': content.get('user_code')}
        task_model = PrintAsyncTaskModel.objects.create(
            task_type=PrintAsyncTaskModel.EXPRESS,
            operator=profile.username,
            params=json.dumps(params))

        print_async_task = PrintAsyncTask.delay(task_model.pk)

        return Response({"task_id": print_async_task, "async_print_id": task_model.pk})

    post = get
