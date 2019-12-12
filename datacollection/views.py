import time
import pymysql.cursors 
import json
import os
import logging 
import datetime
import time
import datacollection.MDCC.UtilityCalc as mdcc


from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.core.files.storage import default_storage
from django.shortcuts import render, HttpResponse
from django.views.generic import TemplateView

from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response

from .forms import UploadFileForm
from datacollection.models import collectlog, file_score, taskitem, feedback_question, user_feedback
from accounts.models import MyUser
from datacollection.serializers import taskitemSerializer, taskAssignSerializer 


#Globle variable
logger = logging.getLogger('fpDataRequest')
logger2 = logging.getLogger('collectLog')
logger3 = logging.getLogger('tasksLog')
logger4 = logging.getLogger('userFeedback')
class campusOutline(TemplateView):
    """To show the campus building information. 
    Url: /api/datacollection/campusoutline
    """
   
    def get(self, request):
        pathToFile = os.path.join(settings.BASE_DIR, 'static/building_dict.json')
        with open(pathToFile) as f:
                term = f.read()
        return HttpResponse(term,content_type="application/json")


class fpData(APIView):
    """This is a API view which handles the general file upload from the mobile side
       (A sample web upload node is availible for get request by rendering upload.html)
       1. receive the post request (with file data saved in 'request.FILES')
       2. extract 3 parameters from the requst ()
       <QueryDict: {u'errorCode': [u'0'], u'file': [], u'buildingName': [u'BSB'], u'floorLevel': [u'2'], u'fileName': [u'dont']}>
       3. save to targeted place according the request fields if not exist create a new then
       4. also log the request info in the logger for debuging purposes
       UploadFileForm has to be used and detail doc is available:
       https://docs.djangoproject.com/en/2.1/topics/http/file-uploads/
    """

    def post(self, request):
        form = UploadFileForm(request.POST, request.FILES)
        print (str(request))
        if form.is_valid():
            logger.info(str(request.POST))
            errorCode = int(request.POST['errorCode'])
            buildingName = str(request.POST['buildingName']) 
            floorLevel= str(request.POST['floorLevel']) 
            fileName = str(request.POST['fileName'])           
            macID = extractMacID(fileName)
            duration = float(request.POST['duration'])
        else:
            logger.debug("At fpData class, an exception was caught:")
            logger.debug("Requese parse failed\n") 
            content = {'status': 2,
                       'message': "Requese parse failed"}
            return Response(content)

        # errorCode is 0 save the file under regular dir    
        if errorCode == 0:
            subPath ='/datacollection/MDCC/FpData/' + buildingName + '/' + floorLevel + '/' + fileName 
            pre_check = default_storage.exists(settings.BASE_DIR+subPath)
            
            if pre_check == True:
                default_storage.delete(settings.BASE_DIR+subPath)
            
            #Saving the file
            default_storage.save((settings.BASE_DIR+subPath), request.FILES['file']) 
            #for calibration file 
            if "Calibration" in fileName:
                return Response({'status':3,'message':'calibration file saved!'})
            #for normal file
            os.chdir(settings.BASE_DIR+'/datacollection/MDCC')
            try:
                #Update task remain time if any
                scale = updateTaskRemain(macID,buildingName,int(floorLevel),duration)
                score = mdcc.utility_calculate(buildingName, int(floorLevel), fileName)
                score = score * scale #Use the scale to adjust
                item = file_score()
                item.Filename = fileName
                item.Score = float(score)
                item.save()
                content = {'status': 0,
                           'message': "save to server success!", 'score':score}
                update_user_score = updateUserScore(macID, item.Score)
                if update_user_score != 0:
                    os.chdir(settings.BASE_DIR)
                    return Response(update_user_score)
                os.chdir(settings.BASE_DIR)
                return Response(content)
            
            except Exception as e:
                logger.debug("At fpData class, an exception was caught:")		
                logger.debug("Fail to save or calculate score: "+str(e)+"\n")
                content = {'status': 1,
       	       	           'message': "fail to calculate score", 'exception':str(e)} 
            os.chdir(settings.BASE_DIR)
            return Response(content)  

        # errorCode is not 0 same the file in the 'erroneous' file under the floor dir
        else: 
            subPath = '/datacollection/MDCC/FpData/' + buildingName + '/' + floorLevel + '/erroneous/' + fileName
            default_storage.save((settings.BASE_DIR+subPath), request.FILES['file'])
            logger.info("Encounter an erroneous file saved under %s\n"%(subPath))
            responseMsg = "File has been saved at %s named %s"%(subPath, fileName)
            content = {'status': 1,
                       'message': "fail to calculate score", 'errorCode':errorCode}
            return Response(content)


class collectLog(APIView):

    def post(self, request):
        # Here add a log later monitoring the traffic
        try:
            logger2.info(str(request.body))
            jsonData = json.loads(request.body)        
            item = collectlog()
            item.MacID = str(jsonData["MacID"])
            item.Mode = int(jsonData["Mode"])
            item.Start_Lat = float(jsonData["Start_Lat"])
            item.Start_Lon = float(jsonData["Start_Lon"])
            item.Terminal_Lat = float(jsonData["Terminal_Lat"])
            item.Terminal_Lon = float(jsonData["Terminal_Lon"])
            item.Errorcode = int(jsonData["Errorcode"])
            item.Building = str(jsonData["Building"])
            item.Floor = int(jsonData["Floor"])
            item.Room = str(jsonData["Room"])
            item.Filename = str(jsonData["Filename"]) 
      
            converted_time = timeConvert(jsonData["Time"], jsonData["Duration"])
            if converted_time['status']:
                return Response(converted_time)
           
            item.Time = converted_time['time']
            item.Duration = converted_time['duration']
            item.save()
            content = {'status': 0,
                       'message':"CollectLog data saves successfully"}

            return Response(content)

        except Exception as e:
            detail = str(e)
            logger2.debug("At collectLog class, an exception was caught:")
            logger2.debug("CollectLog data fails to save: " + detail + "\n")
            content = {'status': 1,
                       'message':"CollectLog data fails to save", 'detail': detail}
         
            return Response(content)


class taskList(APIView):
    serializer_class = taskitemSerializer
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            macid = serializer.data['macid']
            if macid:            
                ctasks = taskitem.objects.filter(MacID = macid)
                if len(ctasks)>0:
                    ret1 = [{'tid':t.ID,'Building':t.Building,'Floor':t.Floor,\
                        'Scale':t.Scale,\
                        'Createtime':time.mktime(t.Createtime.timetuple()),\
                        'Resttime':t.Resttime,\
                        'Accepttime':time.mktime(t.Accepttime.timetuple()),\
                        'Expiretime':time.mktime(t.Expiretime.timetuple())} \
                       for t in ctasks]
                else:
                    ret1=[]
                ptasks =  taskitem.objects.filter(MacID__isnull=True)
                if len(ptasks)>0:
                    ret2 = [{'tid':t.ID,'Building':t.Building,'Floor':t.Floor,\
                      'Scale':t.Scale,\
                      'Createtime':time.mktime(t.Createtime.timetuple()),\
                      'Resttime':t.Resttime} for t in ptasks]
                else:
                    ret2=[]
                return Response({'status':0,'messasge':'query success','ctasks':ret1,\
                                 'ptasks':ret2})
            else:
                return Response({'status':1,'messasge':'Please provide macID!'})        
        return Response({'status':1,'message':'post request is not valid'})


class taskAssign(APIView):
    """Assign tasks to users"""
    serializer_class = taskAssignSerializer
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            macid = serializer.data['macid']
            taskid = serializer.data['taskid']
            try:
                selectedTask = taskitem.objects.get(ID=taskid)
                if selectedTask.MacID:
                    content = {'status':2 ,'message':"This task has been assigned."}
                    return Response(content)   
                elif activeTaskNum(macid)<=2:
                    now = datetime.datetime.now()
                    selectedTask.MacID = macid 
                    selectedTask.Accepttime = now
                    selectedTask.Expiretime = now + datetime.timedelta(hours=24)
                    selectedTask.save()
                    content = {'status':0 ,'message':"Task assigned successfully, please finish in 24 hours."}
                    return Response(content)
                else:
                    content = {'status':3 ,'message':"You have more than 2 active tasks currently."}
                    return Response(content)

            except Exception as e:
                logger3.debug("An exception was caught while assigning task:")
                logger3.debug("Task fails to assign: " + str(e) + "\n")
                content = {'status':4 ,'message':str(e)}
                return Response(content)

        return Response({'status':1,'message':'post request is not valid'})
    

class feedbackQuestion(APIView):
    def get(self, request):
        questions = feedback_question.objects.all()
        content = {}
        for i in questions:
            content[str(i.ID)] = i.Contents
        content ={'status': 0, 'message': json.dumps(content)}
        return Response(content, status=status.HTTP_200_OK)
    def post(self, request):
        try:
            jsonData = json.loads(request.body)
            item = user_feedback()
            item.MacID = str(jsonData["MacID"])
            item.Items = str(jsonData["questions"])
            item.Additional = str(jsonData["comments"])
            item.save()
            content = {'status': 0,
                       'message':"Thank you! Your feedback is received"}
            return Response(content)

        except Exception as e:
            logger4.debug("An exception was caught while receiving user feedback:")
            logger4.debug(str(e) + "\n")
            detail = str(e)
            content = {'status': 1,
                       'message':"Failed to send the feedback to server, please retry later", 'detail': detail}

            return Response(content)
 

def activeTaskNum(macid):
    """Check the number of active tasks for specific user"""
    active_list = []
    now = datetime.datetime.now()
    user_tasklist = taskitem.objects.filter(MacID=macid)
    for task in user_tasklist:
        if task.Expiretime > now and task.Resttime > 1.0:
            active_list.append(task)
    return len(active_list)
   
def extractMacID(filename):
    try:
        macid = filename.split('_')[0]
    except Exception as e:
        return (str(e))
    return macid
     
def updateUserScore(macid, score):
    try:
        user = MyUser.objects.get(macid = macid)
    except Exception as e:
        logger.debug("User can not be found")
        return {'status': 1, 'message': str(e)}
    try:
        current_score = user.score  
        user.score = current_score + score 
        user.save()
    except Exception as e:
        logger.debug("User score fails to update")
        return {'status': 1, 'message': str(e)}
    return 0

def updateTaskRemain(macid,building,floor,duration):
    """UPdate the remain time of a task
       If there exist an active tasks, otherwise do nothing
       Return the scale of the task, if no task, scale 1.0
    """
    userActivetasks = taskitem.objects.filter(MacID=macid,Building = building,\
                      Floor=floor,Expiretime__gte=datetime.datetime.now(),\
                      Resttime__gt = 0)
    if len(userActivetasks) == 0:
        return 1.0
    else:
        task = userActivetasks[0]
        task.Resttime = task.Resttime - duration
        tscale = task.Scale
        task.save()
        return tscale

def timeConvert(time, duration):
    try:
    	time = str(datetime.datetime.fromtimestamp(float(time)/1000).strftime('%Y-%m-%d %H:%M:%S'))
    	duration = str(float(duration)/1000/60) 
    except Exception as e:
        logger2.info("An Exception was caught in collectLog class:")
        logger2.debug("Fail to convert time: " + str(e) + "\n")
        return {'status':1, 'message': "Failed to convert time data"}
    return {'status':0, 'time':time, 'duration': duration}
