from django.shortcuts import render

# Create your views here.

def showWeb(request):
    return render(request, 'webEnd/index.html')
