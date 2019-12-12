import os 
import random
import json

from datetime import datetime
from django.shortcuts import render, redirect
from django.views.generic.base import TemplateView
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import gettext as _
from django.http import Http404

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import TemplateHTMLRenderer

from accounts.models import SignupCode, PasswordResetCode, send_multi_format_email, MyUser
from datacollection.models import collectlog

from accounts.serializers import SignupSerializer, LoginSerializer
from accounts.serializers import PasswordResetSerializer
from accounts.serializers import PasswordResetVerifiedSerializer
from accounts.serializers import PasswordChangeSerializer
from accounts.serializers import UserSerializer
from accounts.forms import SignupWebForm
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import HttpResponse
from django.contrib import messages


# Module Global Variables: 
pathToTemplate = os.path.join(settings.BASE_DIR, 'accounts/templates/')
baseUrl = 'https://mdcc.cas.mcmaster.ca/api/accounts/'
baseUrl2 = 'http://mdcc.cas.mcmaster.ca/api/accounts/'

class Signup(APIView):
    permission_classes = (AllowAny,)
    serializer_class = SignupSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            email = serializer.data['email']
            macid = email.split('@')[0]
            password = serializer.data['password']
            username = serializer.data['username']
            faculty = serializer.data['faculty']
            lable = random.randint(1,6)
            must_validate_email = getattr(settings, "AUTH_EMAIL_VERIFICATION", True)

            try:
                user = get_user_model().objects.get(email=email)
                if user.is_verified:
                    content = {'status': 1, 
                               'message': 'User with this Email address already exists.'}
                    return Response(content, status=status.HTTP_400_BAD_REQUEST)
                try:
                    signup_code = SignupCode.objects.get(user=user)
                    signup_code.delete()
                    pass
                except SignupCode.DoesNotExist:
                    pass
            except get_user_model().DoesNotExist:
                try:
                    user = get_user_model().objects.get(username=username)
                    content = {'status': 3,
                               'message': 'Username already exists.'}
                    return Response(content, status=status.HTTP_400_BAD_REQUEST)
                except get_user_model().DoesNotExist:
                    user = get_user_model().objects.create_user(email=email)

            # Set user fields provided
            user.set_password(password)
            user.username = username
            user.faculty = faculty
            user.lable = lable
            user.macid = macid

            if not must_validate_email:
                user.is_verified = True
                send_multi_format_email('welcome_email', 
                                        {'email': user.email,},
                                        target_email=user.email)
            user.save()

            if must_validate_email:
                # Create and associate signup code
                ipaddr = self.request.META.get('REMOTE_ADDR', '0.0.0.0')
                signup_code = SignupCode.objects.create_signup_code(user, ipaddr)
                signup_code.send_signup_email()

            content = {'status': 0,
                       'message':"A verification email has been sent to %s. Please ensure to check junk box, if you did not receive the email."%(email)}
            return Response(content, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SignupVerify(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        code = request.GET.get('code', '')
        verified = SignupCode.objects.set_user_is_verified(code)

        if verified:
            try:
                signup_code = SignupCode.objects.get(code=code)
                email = signup_code.user.email
#               signup_code.delete()
            except SignupCode.DoesNotExist:
                pass
            content = {'status': 0, 'message': 'User verified.', 'email': email}
            return Response(content, status=status.HTTP_200_OK)
        else:
            content = {'status': 1, 'message': 'Verification Failed.'}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

class DownloadFile(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'profile_list.html'
    def get(self, request):
        requestUrl = str(self.request.get_full_path())
        macid = requestUrl.split('/')[-1]
        caliFile = macid+"_Calibration.pbf"
        queryset = collectlog.objects.filter(MacID=macid, Errorcode=0).exclude(Filename=caliFile)
        return Response({'profiles': queryset})

    def post(self, request):
        print (str(request.POST))
        filePath = str(request.POST['fileName'])
        filePath = settings.BASE_DIR+"/datacollection/MDCC/FpData"+filePath
        print (filePath)
        if os.path.exists(filePath):
            with open(filePath, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(filePath)
            return response
        else:
            raise Http404("file does not exist")





class LoginWeb(APIView):
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer
    template_name = 'login.html'
    def get(self,request):
        return render(request, self.template_name)

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email = serializer.data['email']
            password = serializer.data['password']
            user = authenticate(email=email, password=password)
            try:
                checkEmail = MyUser.objects.get(email=email)
                if user and user.is_verified: 
                    return redirect(baseUrl2+"download/"+user.macid)
                elif user:
                    messages.warning(request._request, 'Email has not been verified')
                    return render(request, self.template_name)
                else:
                    messages.warning(request._request, 'Incorrect password')
                    return render(request, self.template_name)
                   
            except Exception as e:
                messages.warning(request._request, 'Invalid email address')
                return render(request, self.template_name)
        else:
            messages.warning(request._request, 'Invalid email address')
            return render(request, self.template_name)
            


class Login(APIView):
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer

    def post(self, request, format=None):       
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email = serializer.data['email']
            password = serializer.data['password']
            user = authenticate(email=email, password=password)
            try:
                checkEmail = MyUser.objects.get(email=email)
                if user and user.is_verified:
                    token, created = Token.objects.get_or_create(user=user)
                    try:
                        user2 = get_user_model().objects.get(email=email)
                        signup_code = SignupCode.objects.get(user=user2)
                        signup_code.delete()
                        # 0 == true
                        first_time_login = "0"
                    except:
                        first_time_login = "1"

                    user_info = {'macID': user.macid, 'department': user.faculty,
                                 'username': user.username, 'lable': user.lable}
                    content = {'status': 0, 'message':str(token.key), 'data': user_info,
                               'first_time_login':first_time_login}
                    
                    return Response(content, status=status.HTTP_200_OK)
#                    return redirect(baseUrl2+"download/"+user.macid)

                elif user:
                    content = {'status': 2, 'message': 'Unverified email'}
                    return Response(content, status=status.HTTP_401_UNAUTHORIZED)
                else:
                    content = {'status': 3, 'message': 'Incorrect password'}
                    return Response(content, status=status.HTTP_401_UNAUTHORIZED)
            except:
                content = {'status': 1, 'message': 'Invalid email: have not been registered.'} 
                return Response(content, status=status.HTTP_401_UNAUTHORIZED)  
        else:
            return Response(serializer.errors,
                status=status.HTTP_400_BAD_REQUEST) 


class PasswordReset(APIView):
    permission_classes = (AllowAny,)
    serializer_class = PasswordResetSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            email = serializer.data['email']
            try:
                user = get_user_model().objects.get(email=email)
                if user.is_verified and user.is_active:
                    try:
                        password_reset_code = PasswordResetCode.objects.get(user=user)
                        password_reset_code.delete()
                        password_reset_code = \
                            PasswordResetCode.objects.create_reset_code(user)
                        password_reset_code.send_password_reset_email()
                        content = {'status': 0 ,'message':"A verification email has been sent to \
                                   %s, please verify"%(email)}
                        return Response(content, status=status.HTTP_201_CREATED)
                    except:
                        password_reset_code = \
                            PasswordResetCode.objects.create_reset_code(user)
                        password_reset_code.send_password_reset_email()
                        content = {'status': 0, 'message': "Verify successful and an \
                                   email with verification coed has been sent to %s"%(email)}
                        return Response(content, status=status.HTTP_201_CREATED)
            except get_user_model().DoesNotExist:
                pass

            content = {'status': 1, 'message':"Verify failed: the email has been not registered"}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors,
                status=status.HTTP_400_BAD_REQUEST)


class PasswordResetVerified(APIView):
    permission_classes = (AllowAny,)
    serializer_class = PasswordResetVerifiedSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            code = serializer.data['code']
            password = serializer.data['password']

            try:
                password_reset_code = PasswordResetCode.objects.get(code=code)
                password_reset_code.user.set_password(password)
                password_reset_code.user.save()
                password_reset_code.delete()
                content = {'status': 0, 'message': "Password reset"}
                return Response(content, status=status.HTTP_200_OK)
            except PasswordResetCode.DoesNotExist:
                content = {'status': 1, 'message': "Verification code is incorrect."}
                return Response(content, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response(serializer.errors,
                status=status.HTTP_400_BAD_REQUEST)

class DisplayLeaderboard(APIView):

    def get(self, request):
        try:
            content={}
            users = MyUser.objects.exclude(score = 0.0)
            #users = MyUser.objects.all()
            top_users = users.exclude(macid='admin').order_by('-score')[:50]
            rank_position = 1
            for i in top_users:
                content[str(rank_position)] = str(i.username) +"-" + str(float("{0:.2f}".format(i.score)))
                rank_position = rank_position + 1 
            content ={'status': 0, 'message': json.dumps(content)}    
            return Response(content, status=status.HTTP_200_OK)
        except Exception as e:
            content = {'status':1, 'message': e}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)



"""
Below are Classes to provice Website services 

"""
class DisplayMap(TemplateView):
    """Class to render the mapbox api map"""
    template_name = 'displayMap.html'
    
    def get(self,request):
        return render(request, self.template_name)


class DisplayPolicy(TemplateView):
    """Class to render the Term&Policy HTML page"""
    template_name = 'displayPolicy.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        response = request.POST
        try:
            response['checkbox']
        except: 
            return render(request, self.template_name)
        return redirect(baseUrl2 + 'register/')
        
          
class RegisterInfo(TemplateView):
    """Class to provide signup services on the website"""
    template_name = 'registerInfo.html'
   
    def get(self, request):
        form = SignupWebForm()
        return render(request, self.template_name, {'form':form})
    
    def post(self, request, format=None):
        form = SignupWebForm(request.POST)
        # Validate the user registeration infor is correct
        if form.is_valid():
            email = form.data['email']
            password = form.data['password']
            username = form.data['username']
            faculty = form.data['faculty']
            must_validate_email = getattr(settings, "AUTH_EMAIL_VERIFICATION", True)
            verify_email = email.split('@')[0]
            print (verify_email)
            #Start creating a new user
            user = get_user_model().objects.create_user(email=email)
            user.set_password(password)
            user.username = username
            user.faculty = faculty
  
            if not must_validate_email:
                user.is_verified = True
                send_multi_format_email('welcome_email', 
                                        {'email': user.email,},
                                        target_email=user.email)
            user.save()
  
            # send out the verification email and generate a signup code 
            if must_validate_email:
                # Create and associate signup code
                ipaddr = self.request.META.get('REMOTE_ADDR', '0.0.0.0')
                signup_code = SignupCode.objects.create_signup_code(user, ipaddr)
                signup_code.send_signup_email()
            return render(request,'displayQRcode.html')

        # User registeration infor is not correct 
        else:
            args = {'form':form}
            return render(request, self.template_name, args)


