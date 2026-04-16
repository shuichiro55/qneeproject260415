# your_app/tasks.py
from celery import shared_task
from . import views

@shared_task
def add(x, y):
  print(f"結果: {x + y}")
  print('Hello!')
  return x + y

@shared_task
def sendServInfoMailNow():
  views.InvitationAgtView.sendNow()
  print('pass send SerInfoMail in tasks.py of send! ')
  return 1