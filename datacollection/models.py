from django.db import models
from django.utils.timezone import now

class file_score(models.Model):
    Filename = models.CharField('Filename', max_length=125, null=True, blank=False,
        unique=False)
    Score = models.FloatField('Score', null=True, blank=False,
        unique=False)
    def __str__(self):
        return self.Filename 

class collectlog(models.Model):
    ID = models.AutoField( 'ID', auto_created=True, primary_key=True)
    MacID = models.CharField('MacID', max_length=30, null=True,
        blank=False, unique=False)
    Mode = models.IntegerField('Mode', blank=True, unique=False,
        null=True)
    Time = models.DateTimeField('Time', blank=True, default=now)
    Duration = models.CharField('Duration', max_length=30, null=True,
        blank=False, unique=False) 
    Start_Lat = models.FloatField('Start_Lat', null=True, blank=False, 
        unique=False)    
    Start_Lon = models.FloatField('Start_Lon', null=True, blank=False, 
        unique=False)
    Terminal_Lat = models.FloatField('Terminal_Lat', null=True, blank=False,
        unique=False) 
    Terminal_Lon = models.FloatField('Terminal_Lon', null=True, blank=False,
        unique=False)
    Errorcode = models.IntegerField('Errorcode', blank=True, unique=False,
        null=True)
    Building = models.CharField('Building', max_length=30, null=True, blank=False, 
        unique=False)
    Floor = models.IntegerField('Floor', blank=True, unique=False, null=True)
    Room = models.CharField('Room', max_length=30, null=True, blank=False, 
        unique=False)
    Filename = models.CharField('Filename', max_length=125, null=True, blank=False,
        unique=False)

    def __str__(self):
        return self.MacID

class feedback_question(models.Model):
    ID = models.AutoField( 'ID', auto_created=True, primary_key=True)
    Contents = models.TextField('Question', max_length=300, null=True, blank=True,
        unique=False)
class user_feedback(models.Model):
    ID = models.AutoField( 'ID', auto_created=True, primary_key=True)
    MacID = models.CharField('MacID', max_length=30, null=True,
        blank=False, unique=False)
    Items = models.CharField('Clicked_item', max_length=125, null=True, blank=True,
        unique=False)
    Additional = models.TextField('Comments', max_length=300, null=True, blank=True,
        unique=False)
    Time = models.DateTimeField('Time', blank=True, default=now)

#class file_score(models.Model):
#    Filename = models.CharField('Filename', max_length=125, null=True, blank=False,
#        unique=False)
#    Score = models.FloatField('Score', null=True, blank=False,
#        unique=False) 
class taskitem(models.Model):
    #Task information
    ID = models.AutoField( 'ID', auto_created=True, primary_key=True)
    Building = models.CharField('Building', max_length=30, null=True,\
	       blank=False,unique=False)
    Floor = models.IntegerField('Floor', blank=True, unique=False, null=True)
    Scale = models.FloatField('Scale', null=False, blank=False,
        unique=False,default = 1.0)
    Createtime = models.DateTimeField('Createtime', blank=True, default=now)
    Resttime = models.FloatField('Resttime', blank=False,unique=False, default = 30.0)
    #User information, can be null if no user picks the task
    MacID = models.CharField('MacID', max_length=30, null=True,
        blank=False, unique=False)
    Accepttime = models.DateTimeField('Accepttime', blank=True, null = True)
    Expiretime = models.DateTimeField('Expiretime', blank=True, null = True)

