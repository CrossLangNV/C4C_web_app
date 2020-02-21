import os
from uuid import uuid4

from django.db.models.signals import post_save
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.detail import ContextMixin, TemplateResponseMixin
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from scrapyd_api import ScrapydAPI

from .models import ScrapyItem
from .serializers import ScrapyItemSerializer


@method_decorator(csrf_exempt, name='dispatch')
class ScrapingTemplateView(View, ContextMixin, TemplateResponseMixin):
    template_name = "scraping/scraping.html"
    scrapyd = ScrapydAPI(os.environ['SCRAPYD_URL'])

    # query db for scraped item
    def get(self, request):
        unique_id = request.GET.get('unique_id', None)

        if not unique_id:
            # render overview page
            scraped_items = ScrapyItem.objects.all()
            serializer = ScrapyItemSerializer(scraped_items, many=True)
            return render(request, self.template_name, {'scraped_items': serializer.data})

        try:
            # this is the unique_id that we created even before crawling started.
            item = ScrapyItem.objects.get(unique_id=unique_id)
            serializer = ScrapyItemSerializer(item)
            return JsonResponse(serializer.data)
        except Exception as e:
            return JsonResponse({'error': str(e)})

    # new scraping task
    def post(self, request, spider):
        if not spider:
            return JsonResponse({'error': 'Missing spider'})

        unique_id = str(uuid4())  # create a unique ID

        # custom settings for spider
        settings = {
            'unique_id': unique_id,
            'spider': spider,
            'USER_AGENT': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
        }

        # schedule scraping task
        task = self.scrapyd.schedule('default', spider, settings=settings)

        return JsonResponse({'task_id': task, 'unique_id': unique_id, 'status': 'started'})


class ScrapingItemList(ListAPIView):
    queryset = ScrapyItem.objects.all()
    serializer_class = ScrapyItemSerializer

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = ScrapyItemSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ScrapyItemSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'serializer': serializer})
        serializer.save()
        return redirect('scraping:scraping-task')

class PostprocessScrapyItem(APIView):

    def post(self, request, *args, **kwargs):
        scrapy_item = ScrapyItem.objects.get(pk=kwargs['pk'])
        post_save.send(ScrapyItem, instance=scrapy_item, created=True)
        return redirect('searchapp:websites')
