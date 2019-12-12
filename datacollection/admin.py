from django.contrib import admin
from .models import user_feedback, feedback_question, collectlog, file_score, taskitem
# Register your models here.



class collectlogAdmin(admin.ModelAdmin):
 	"""docstring for Pathmagfp"""
 	fieldsets = (('Collect Log', {'fields': ('MacID', 'Mode', 
            'Time', 'Duration', 'Start_Lat', 'Start_Lon', 'Terminal_Lat', 'Terminal_Lon',
            'Errorcode', 'Building', 'Floor', 'Room', 'Filename')},),)

 	list_display = ('ID','MacID', 'Time')
 	ordering = ('Time',)

class fileScoreAdmin(admin.ModelAdmin):
        """docstring for Pathmagfp"""
        fieldsets = (('File Score', {'fields': ('Filename', 'Score',)},),)
        list_display = ('Filename','Score')

class taskitemAdmin(admin.ModelAdmin):
        """docstring for Pathmagfp"""
        fieldsets = (('Task Item', {'fields': ( 'MacID', 'Building', 'Floor', 'Scale', 
            'Createtime', 'Resttime', 'Accepttime','Expiretime')},),)

        list_display = ('ID','MacID')
        ordering = ('ID',)

class feedbackQuestionAdmin(admin.ModelAdmin):
        """docstring for Pathmagfp"""
        fieldsets = (('Question', {'fields': ('Contents',)},),)

        list_display = ('ID','Contents')
        ordering = ('ID',)


class userFeedbackAdmin(admin.ModelAdmin):
        """docstring for Pathmagfp"""
        fieldsets = (('User Feedback', {'fields': ('MacID', 'Items', 'Additional',
            'Time')},),)
        list_display = ('ID','MacID','Items','Additional','Time')
        ordering = ('ID',)
      
admin.site.register(file_score, fileScoreAdmin)
admin.site.register(collectlog, collectlogAdmin)
admin.site.register(taskitem, taskitemAdmin)
admin.site.register(user_feedback, userFeedbackAdmin)
admin.site.register(feedback_question, feedbackQuestionAdmin)

