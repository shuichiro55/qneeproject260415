from django.shortcuts import render,redirect
from contact.models import Contact
from django.http.response import JsonResponse
from django.core.mail import send_mail
from django.views.generic.base import View
from django.contrib import messages
# Contact Form

class Contactus(View):
    def post(self,request):
        if request.method == "POST":
            name = request.POST["name"]
            email = request.POST["email"]
            subject = request.POST["subject"]
            comment = request.POST["comments"]
            print("name :",name,"email :",email,"subject:",subject,"comment:",comment)
            messages.success(request, name)
            c = Contact()
            c.name=name,
            c.email=email,
            c.subject=subject,
            c.comment=comment,
            c.save()
            if name and email and subject and comment != "":
                subject = "Thank You"
                from_mail = 'kucra@support.com'
                message = "Thank you for contact us"
                send_mail(subject, message, from_mail, [email],fail_silently=False)
            return redirect("/#contact")
