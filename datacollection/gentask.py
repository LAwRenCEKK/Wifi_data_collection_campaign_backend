import sys,os,django
#Set django env
project_root_path = os.path.realpath(os.path.dirname(os.path.abspath(__file__))+'/..')
sys.path.append(project_root_path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'mdccBackend.settings' 
django.setup()
#import models
from datacollection.models import taskitem
import time
if __name__=='__main__':
    print('hello')
    #create
    #taskitem.objects.create(Building='ABB',Floor=1,Scale=2.0,Resttime=5.0)
    #taskitem.objects.create(Building='HH',Floor=1,Scale=2.0,Resttime=5.0)
    #taskitem.objects.create(Building='BSB',Floor=1,Scale=2.0,Resttime=5.0)
    #taskitem.objects.create(Building='ETB',Floor=1,Scale=1.0,Resttime=5.0)
    #taskitem.objects.create(Building='ETB',Floor=2,Scale=1.0,Resttime=5.0)
    #taskitem.objects.create(Building='JHE',Floor=1,Scale=2.0,Resttime=5.0)
    #taskitem.objects.create(Building='JHE',Floor=2,Scale=2.0,Resttime=5.0)
    #taskitem.objects.create(Building='JHE',Floor=3,Scale=1.0,Resttime=5.0)
    tasks = taskitem.objects.all()
    print(str(tasks[0]))
    #query
    tids = []
    for task in tasks:
        tids.append(task.ID)
    print(tids)
    #delete
    #taskitem.objects.filter(ID=1).delete()
    #update
    #taskitem.objects.filter(ID=5).update(MacID='weiy49')
    from datetime import datetime, timedelta
    #taskitem.objects.filter(ID=5).update(Accepttime=datetime.now())
    #taskitem.objects.filter(ID=2).update(Expiretime=datetime.now()+timedelta(days=2))
    #taskitem.objects.filter(ID=5).update(Resttime = 0.5)
    #taskitem.objects.filter(ID=10).update(Resttime = 10.5)
    #taskitem.objects.filter(ID=2).update(MacID=None)
    #taskitem.objects.filter(ID=5).update(MacID = None)
    #taskitem.objects.filter(ID=10).update(MacID = None)
    #query
    tasks = taskitem.objects.filter(MacID = 'weiy49')
    for t in tasks:
        print(type(t.Createtime))
        print(t.Createtime)
        print(time.mktime(t.Createtime.timetuple()))
    #query user with active taks
    #tasks = taskitem.objects.filter(MacID='weiy49',Building = 'JHE',Floor=3,Expiretime__gte=datetime.now())
    #print(len(tasks))
    #print(tasks[0].ID)
