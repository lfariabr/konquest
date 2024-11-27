from django.shortcuts import render

def home(request):
    # return render(request, '/templates/pages/home.html')
    return render(request, 'pages/home.html')
