'''1. this app contains all the urls regarding files/data transfer
        1) fileupload
   '''

from django.conf.urls import url, include
from . import views 


urlpatterns =(
    url(r'^campusoutline/', views.campusOutline.as_view()),
    url(r'^fpDataUpload/', views.fpData.as_view()),
    url(r'^collectlog/', views.collectLog.as_view()),
    url(r'^tasklist/', views.taskList.as_view()),
    url(r'^taskassign/', views.taskAssign.as_view()),
    url(r'^feedbackquestion/', views.feedbackQuestion.as_view()),    
)
