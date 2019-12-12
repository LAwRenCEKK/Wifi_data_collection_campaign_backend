from django import forms

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.forms import UserChangeForm
from django.utils.translation import ugettext_lazy as _

from accounts.models import MyUser


class EmailUserCreationForm(forms.ModelForm):
    """A form that creates a user, with no privileges, from the given email and
    password.
    """
    username = forms.CharField(label=_('user name'),)
    password1 = forms.CharField(label=_('Password'), 
        widget=forms.PasswordInput)
    password2 = forms.CharField(label=_('Password confirmation'),
        widget=forms.PasswordInput,
        help_text=_('Enter the same password as above, for verification.'))

    class Meta:
        model = get_user_model()
        fields = ('email',)
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        try:
            get_user_model().objects.get(email=email)
        except get_user_model().DoesNotExist:
            return email
        raise forms.ValidationError(_('A user with that email already exists.'))

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                _('The two password fields did not match.'))
        return password2

    def save(self, commit=True):
        user = super(EmailUserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class EmailUserChangeForm(UserChangeForm):
    username = forms.CharField(label = ('username'))

    class Meta:
        model = get_user_model()
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(EmailUserChangeForm, self).__init__(*args, **kwargs)


class SignupWebForm(forms.ModelForm):
    """Website signup form"""
    password = forms.CharField(label='Password', widget=forms.PasswordInput)

    class Meta:
        model = MyUser 
        fields = {'username','faculty','email', 'password'}
        field_order = ['username', 'email', 'password', 'faculty']
    
    def __init__(self, *args, **kwargs):
        super(SignupWebForm, self).__init__(*args, **kwargs)
        self.fields['password'].widget.attrs.update(
            {'placeholder': 'Your Password'})
        self.fields.keyOrder = ['username', 'email', 'password', 'faculty'] 

    def clean_password(self):
        password = self.cleaned_data['password']
        if len(password) < 6:
            raise forms.ValidationError("The password is too short")
        return password


    def clean_email(self):
        email = self.cleaned_data['email']
        if "@mcmaster.ca" not in email:
            raise forms.ValidationError("Please use @mcmaster.ca email to register")
        return email
