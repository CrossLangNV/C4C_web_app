import os

from django.db.models.signals import post_save
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.detail import ContextMixin, TemplateResponseMixin
from rest_framework.generics import ListAPIView, ListCreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from scrapyd_api import ScrapydAPI

from .models import ScrapingTask, ScrapingTaskItem
from .serializers import ScrapingTaskItemSerializer, ScrapingTaskSerializer


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


class ScrapingTaskListView(ListCreateAPIView):
    queryset = ScrapingTask.objects.all()
    serializer_class = ScrapingTaskSerializer
    scrapyd = ScrapydAPI(os.environ['SCRAPYD_URL'])
    scrapyd_project = 'default'

    def get(self, request, *args, **kwargs):
        # get tasks + status per task
        queryset = self.get_queryset()
        serializer_read = ScrapingTaskSerializer(queryset, many=True)
        for task_data in serializer_read.data:
            if task_data['scheduler_id']:
                status = self.scrapyd.job_status(self.scrapyd_project, task_data['scheduler_id'])
                task = ScrapingTask.objects.get(pk=task_data['id'])
                task.status = status
                task.save()
        return Response(serializer_read.data)

    def post(self, request, *args, **kwargs):
        # launch scraping task
        serializer = ScrapingTaskSerializer(data=request.data)
        if serializer.is_valid():
            scraping_task = serializer.save()
            # custom settings for spider
            settings = {
                'task_id': scraping_task.id,
                'USER_AGENT': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
            }
            scheduler_id = self.scrapyd.schedule(self.scrapyd_project, scraping_task.spider, settings=settings,
                                                 spider_type=scraping_task.spider_type)
            scraping_task.scheduler_id = scheduler_id
            scraping_task.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


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


class PostprocessScrapingTask(APIView):

    def post(self, request, *args, **kwargs):
        scraping_task = ScrapingTask.objects.get(pk=kwargs['pk'])
        scraping_task_items = scraping_task.items.all()
        for item in scraping_task_items:
            post_save.send(ScrapingTaskItem, instance=item, created=True)
        return redirect('searchapp:websites')
