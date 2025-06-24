from django.shortcuts import render
from django.http import HttpResponse, HttpRequest
def menu(request:HttpRequest):
    return render(request,"menu.html")
