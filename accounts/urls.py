from django.conf.urls import patterns, url, include
from rest_framework.urlpatterns import format_suffix_patterns
from accounts import views
urlpatterns = [
    url(r'^signup/$', views.Signup.as_view(), name='signup'),
    url(r'^signup/verify/$', views.SignupVerify.as_view(),
        name='authemail-signup-verify'),

    url(r'^login/$', views.Login.as_view(), name='authemail-login'),
    url(r'^password/reset/$', views.PasswordReset.as_view(), 
        name='authemail-password-reset'),
    url(r'^password/reset/verified/$', views.PasswordResetVerified.as_view(), 
        name='authemail-password-reset-verified'),

    url(r'^home/$', views.DisplayPolicy.as_view(), name='website-home'),
    url(r'^register/$', views.RegisterInfo.as_view(), name='website-register'),
    url(r'^displaymap/$',views.DisplayMap.as_view(), name='website-display-map'),
    url(r'^leaderboard/$', views.DisplayLeaderboard.as_view(), name='display-leaderboard'),
    url(r'^download/', views.DownloadFile.as_view(), name='download-file'),
    url(r'^weblogin/$', views.LoginWeb.as_view(), name='web-login'),

    ]


urlpatterns = format_suffix_patterns(urlpatterns)
