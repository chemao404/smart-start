from django.shortcuts import render, redirect
def index(request):
    return render(request, 'index.html')
# Create your views here.
