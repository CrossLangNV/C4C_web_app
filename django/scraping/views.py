import os

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

from .models import ScrapingTask
from .serializers import ScrapingTaskSerializer


@method_decorator(csrf_exempt, name='dispatch')
class ScrapingTemplateView(View, ContextMixin, TemplateResponseMixin):
    template_name = "scraping/scraping.html"
    scrapyd = ScrapydAPI(os.environ['SCRAPYD_URL'])
    scrapyd_project = 'default'

    def get(self, request):
        # render overview page
        scraped_tasks = ScrapingTask.objects.all()
        # FIXME: get list from http://localhost:6800/listspiders.json?project=default ?
        spiders = [{"id": "bis"}, {"id": "eiopa"}, {"id": "esma"}, {
            "id": "eurlex", "type": "directions"}, {"id": "eurlex", "type": "decisions"}, {"id": "eurlex", "type": "regulations"}, {"id": "fsb"}, {"id": "srb"},
            {"id": "eba", "type": "guidelines"}, {
                "id": "eba", "type": "recommendations"},
        ]
        return render(request, self.template_name, {'scraped_tasks': scraped_tasks, 'nav': 'scraping', 'spiders': spiders})

    # new scraping task
    def post(self, request, spider):
        spider_type = request.POST.get('spider_type')
        if not spider_type:
            return JsonResponse({'error': 'Missing spider type'})

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
            self.scrapyd_project, spider, settings=settings)

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
        # get tasks + status per task
        queryset = self.get_queryset()
        serializer_read = ScrapingTaskSerializer(queryset, many=True)
        for task_data in serializer_read.data:
            if task_data['scheduler_id']:
                status = self.scrapyd.job_status(
                    self.scrapyd_project, task_data['scheduler_id'])
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
                'task_id': scraping_task.id
            }
            scheduler_id = self.scrapyd.schedule(self.scrapyd_project, scraping_task.spider, settings=settings,
                                                 spider_type=scraping_task.spider_type)
            scraping_task.scheduler_id = scheduler_id
            scraping_task.save()
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
        if task.scheduler_id:
            status = self.scrapyd.job_status(
                self.scrapyd_project, task.scheduler_id)
            task.status = status
            task.save()
        return task


class SpiderListView(APIView):
    scrapyd = ScrapydAPI(os.environ['SCRAPYD_URL'])
    scrapyd_project = 'default'

    def get(self, request, *args, **kwargs):
        spiders = self.scrapyd.list_spiders(self.scrapyd_project)
        return Response(spiders)
