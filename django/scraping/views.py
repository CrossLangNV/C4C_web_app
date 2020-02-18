import os
from uuid import uuid4

from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.detail import ContextMixin, TemplateResponseMixin
from scrapyd_api import ScrapydAPI

from .models import ScrapyItem


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
            return render(request, self.template_name, {'scraped_items': scraped_items})

        try:
            # this is the unique_id that we created even before crawling started.
            item = ScrapyItem.objects.get(unique_id=unique_id)
            return JsonResponse({'data': item.to_dict['data']})
        except Exception as e:
            return JsonResponse({'error': str(e)})

    # new scraping task
    def post(self, request, spider):
        #spider = request.POST.get('spider', None)

        if not spider:
            return JsonResponse({'error': 'Missing spider'})

        unique_id = str(uuid4())  # create a unique ID

        # custom settings for spider
        settings = {
            'unique_id': unique_id,
            'USER_AGENT': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
        }

        # schedule scraping task
        task = self.scrapyd.schedule('default', spider, settings=settings)

        return JsonResponse({'task_id': task, 'unique_id': unique_id, 'status': 'started'})
