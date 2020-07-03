import logging
from datetime import datetime

from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

from scheduler.tasks import launch_crawler
from .models import ScrapingTask, ScrapingTaskItem
from .serializers import ScrapingTaskSerializer

logger = logging.getLogger(__name__)


class ScrapingTaskListView(CreateAPIView):
    queryset = ScrapingTask.objects.all()
    serializer_class = ScrapingTaskSerializer

    def post(self, request, *args, **kwargs):
        # launch scraping task
        serializer = ScrapingTaskSerializer(data=request.data)
        if serializer.is_valid():
            scraping_task = serializer.save()
            if scraping_task.spider_date_start and scraping_task.spider_date_end:
                date_start = scraping_task.spider_date_start.strftime('%d%m%Y')
                date_end = scraping_task.spider_date_end.strftime('%d%m%Y')
                celery_task = launch_crawler.delay(scraping_task.spider,
                                                   scraping_task.spider_type,
                                                   date_start,
                                                   date_end)
                ScrapingTaskItem.objects.create(scheduler_id=celery_task.id, task=scraping_task)

            elif scraping_task.spider == 'eurlex':
                # launch spider per 10 years
                year_stop = 1959
                today = datetime.today()
                for year in range(today.year, year_stop, -10):
                    start = '0101' + str(year - 9)
                    end = '3112' + str(year)
                    celery_task = launch_crawler.delay(scraping_task.spider,
                                                       scraping_task.spider_type,
                                                       scraping_task.id,
                                                       start,
                                                       end)
                    ScrapingTaskItem.objects.create(scheduler_id=celery_task.id, task=scraping_task)
            else:
                celery_task = launch_crawler.delay(scraping_task.spider,
                                                   scraping_task.spider_type,
                                                   None,
                                                   None)
                ScrapingTaskItem.objects.create(scheduler_id=celery_task.id, task=scraping_task)
            return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)
