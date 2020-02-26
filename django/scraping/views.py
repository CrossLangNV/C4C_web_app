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

from .models import ScrapingTask, ScrapingTaskItem
from .serializers import ScrapingTaskItemSerializer


@method_decorator(csrf_exempt, name='dispatch')
class ScrapingTemplateView(View, ContextMixin, TemplateResponseMixin):
    template_name = "scraping/scraping.html"
    scrapyd = ScrapydAPI(os.environ['SCRAPYD_URL'])

    def get(self, request):
        # render overview page
        scraped_tasks = ScrapingTask.objects.all()
        return render(request, self.template_name, {'scraped_tasks': scraped_tasks, 'nav': 'scraping'})

    # new scraping task
    def post(self, request, spider):
        if not spider:
            return JsonResponse({'error': 'Missing spider'})

        scraping_task = ScrapingTask.objects.create(
            spider=spider
        )
        scraping_task.save()

        # custom settings for spider
        settings = {
            'task_id': scraping_task.id,
            'USER_AGENT': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
        }

        # schedule scraping task
        scrapyd_task_id = self.scrapyd.schedule('default', spider, settings=settings)

        return redirect('scraping:scraping')


class ScrapingTaskListView(ListAPIView):
    queryset = ScrapingTaskItem.objects.all()
    serializer_class = ScrapingTaskItemSerializer

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = ScrapingTaskItemSerializer(queryset, many=True)
        return Response(serializer.data)


class ScrapingTaskView(APIView):

    def get(self, request, *args, **kwargs):
        # get all items for this scraping task
        scraping_task = ScrapingTask.objects.get(pk=kwargs['pk'])
        scraping_items = scraping_task.items.all()
        serializer = ScrapingTaskItemSerializer(scraping_items, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        # add scraping item to scraping task
        serializer = ScrapingTaskItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
        return redirect('scraping:scraping-task-list')


class PostprocessScrapingItem(APIView):

    def post(self, request, *args, **kwargs):
        scraping_item = ScrapingTaskItem.objects.get(pk=kwargs['pk'])
        post_save.send(ScrapingTaskItem, instance=scraping_item, created=True)
        return redirect('searchapp:websites')
