from django.shortcuts import render, redirect
from .solr_call import solr_search, solr_search_id, solr_add
from django.contrib.auth import login, logout
import uuid

from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Document, Website
from .forms import CreateDocument

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required

@login_required(login_url='login')
def search_index(request):
    search_term = "*"
    if request.GET.get('term'):
        search_term = request.GET['term']

    results = solr_search(core="films", term=search_term)
    print(results)
    context = {'results': results, 'count': len(results), 'search_term': search_term}
    return render(request, 'index.html', context)

@login_required(login_url='login')
def website_list(request):
    websites = Website.objects.all()

    return render(request, 'website_list.html', {'websites': websites})

@login_required(login_url='login')
def website_detail(request, id):
    website = Website.objects.get(pk=id)
    documents = Document.objects.all().filter(website = id)
    for doc in documents:
        found_solr_docs = solr_search_id('documents', str(doc.id))
        if len(found_solr_docs) > 0:
            doc.solr_data = found_solr_docs[0]

    return render(request, 'website_detail.html', {'website': website, 'documents': documents})

@login_required(login_url='login')
def document_create(request, website_id):
    form = CreateDocument()
    if request.method == 'POST':
        form = CreateDocument(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            # cd contains form data as dictionary
            generated_doc_id = uuid.uuid4()
            new_document = Document.objects.create(
                id = generated_doc_id,
                title = cd.get('title'),
                date = cd.get('date'),
                acceptance_state = cd.get('acceptance_state'),
                url = cd.get('url'),
                website = Website.objects.get(pk=website_id)
            )
            new_document.save()
            # add and index to Solr
            solr_doc = {
                "id": str(generated_doc_id),
                "content": [cd.get('content')]
            }
            solr_add(core="documents", docs=[solr_doc])
            return redirect('website', id = website_id)

    return render(request, 'document_create.html', {'form': form, 'website_id': website_id})

@login_required(login_url='login')
def document_list(request):
    documents = Document.objects.all().order_by('date')
    for doc in documents:
        doc.solr_data = solr_search_id('documents', str(doc.id))

    return render(request, 'document_list.html', {'documents': documents})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('websites')
    elif request.method == 'GET':
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('websites')

class FilmList(APIView):
    """
    View all films.
    """
    def get(self, request, format=None):
        """
        Return a list of all films.
        """
        films = solr_search(core="films", term="*")
        return Response(films)

class Film(APIView):
    """
    Search for a film.
    """
    def get(self, request, search_term, format=None):
        """
        Return a list of found films.
        """
        films = solr_search(core="films", term=search_term)
        return Response(films)

