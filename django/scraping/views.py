import os

import logging
from datetime import datetime

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.detail import ContextMixin, TemplateResponseMixin
from rest_framework.generics import ListCreateAPIView, RetrieveDestroyAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from scrapyd_api import ScrapydAPI

from .models import ScrapingTask, ScrapingTaskItem
from .serializers import ScrapingTaskSerializer

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class ScrapingTemplateView(View, ContextMixin, TemplateResponseMixin):
    template_name = "scraping/scraping.html"
    scrapyd = ScrapydAPI(os.environ['SCRAPYD_URL'])
    scrapyd_project = 'default'

    def get(self, request):
        # render overview page
        scraped_tasks = ScrapingTask.objects.all().order_by("-date")
        # FIXME: get list from http://localhost:6800/listspiders.json?project=default ?
        spiders = [{"id": "bis"}, {"id": "eiopa"}, {"id": "esma"}, {
            "id": "eurlex", "type": "directives"}, {"id": "eurlex", "type": "decisions"},
                   {"id": "eurlex", "type": "regulations"}, {"id": "fsb"}, {"id": "srb"},
                   {"id": "eba", "type": "guidelines"}, {
                       "id": "eba", "type": "recommendations"},
                   ]
        return render(request, self.template_name,
                      {'scraped_tasks': scraped_tasks, 'nav': 'scraping', 'spiders': spiders})

    # new scraping task
    def post(self, request, spider):
        spider_type = request.POST.get('spider_type')
        logger.info("Starting spider: " + spider +
                    " with type: " + spider_type)

        if not spider:
            return JsonResponse({'error': 'Missing spider'})

        scraping_task = ScrapingTask.objects.create(
            spider=spider,
            spider_type=spider_type

        )
        scraping_task.save()

        # custom settings for spider
        settings = {
            'task_id': scraping_task.id,
            'USER_AGENT': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
        }

        # schedule scraping task
        scrapyd_task_id = self.scrapyd.schedule(
            self.scrapyd_project, spider, settings=settings, spider_type=spider_type)

        # Store the scheduler_id
        scraping_task.scheduler_id = scrapyd_task_id
        scraping_task.save()

        return redirect('scraping:scraping')


class ScrapingTaskListView(ListCreateAPIView):
    queryset = ScrapingTask.objects.all()
    serializer_class = ScrapingTaskSerializer
    scrapyd = ScrapydAPI(os.environ['SCRAPYD_URL'])
    scrapyd_project = 'default'

    def get(self, request, *args, **kwargs):
        # get tasks + status per task item
        queryset = self.get_queryset()
        serializer_read = ScrapingTaskSerializer(queryset, many=True)
        tasks = serializer_read.data
        for task in tasks:
            for item_data in task['items']:
                status = self.scrapyd.job_status(self.scrapyd_project, item_data['scheduler_id'])
                item = ScrapingTaskItem.objects.get(pk=item_data['id'])
                item.status = status
                item.save()
        return Response(serializer_read.data)

    def post(self, request, *args, **kwargs):
        # launch scraping task
        serializer = ScrapingTaskSerializer(data=request.data)
        if serializer.is_valid():
            scraping_task = serializer.save()
            # custom settings for spider
            settings = {
                'task_id': scraping_task.id
            }
            if scraping_task.spider_date_start and scraping_task.spider_date_end:
                date_start = scraping_task.spider_date_start.strftime('%d%m%Y')
                date_end = scraping_task.spider_date_end.strftime('%d%m%Y')
                scheduler_id = self.scrapyd.schedule(self.scrapyd_project, scraping_task.spider, settings=settings,
                                                     spider_type=scraping_task.spider_type,
                                                     spider_date_start=date_start,
                                                     spider_date_end=date_end)
                ScrapingTaskItem.objects.create(scheduler_id=scheduler_id, task=scraping_task)

            else:
                # launch spider per 10 years
                year_stop = 1959
                today = datetime.today()
                for year in range(today.year, year_stop, -10):
                    start = '0101' + str(year - 10)
                    end = '3112' + str(year)
                    scheduler_id = self.scrapyd.schedule(self.scrapyd_project, scraping_task.spider, settings=settings,
                                                         spider_type=scraping_task.spider_type,
                                                         spider_date_start=start,
                                                         spider_date_end=end)
                    ScrapingTaskItem.objects.create(scheduler_id=scheduler_id, task=scraping_task)
                return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)


class ScrapingTaskView(RetrieveDestroyAPIView):
    queryset = ScrapingTask.objects.all()
    serializer_class = ScrapingTaskSerializer
    scrapyd = ScrapydAPI(os.environ['SCRAPYD_URL'])
    scrapyd_project = 'default'

    def get_object(self):
        # update with status
        queryset = self.get_queryset()
        task_qs = queryset.filter(pk=self.kwargs['pk'])
        task = task_qs[0]
        for item in task.items.all():
            status = self.scrapyd.job_status(self.scrapyd_project, item.scheduler_id)
            item.status = status
            item.save()
        return task


class SpiderListView(APIView):
    scrapyd = ScrapydAPI(os.environ['SCRAPYD_URL'])
    scrapyd_project = 'default'

    def get(self, request, *args, **kwargs):
        spiders = self.scrapyd.list_spiders(self.scrapyd_project)
        return Response(spiders)
