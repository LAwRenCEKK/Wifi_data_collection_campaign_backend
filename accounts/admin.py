from __future__ import absolute_import

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext, ugettext_lazy as _

from accounts.forms import EmailUserCreationForm, EmailUserChangeForm
from accounts.models import SignupCode, PasswordResetCode, MyUser

class SignupCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'user', 'ipaddr', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('user', 'code', 'ipaddr')

    def has_add_permission(self, request):
        return False


class SignupCodeInline(admin.TabularInline):
    model = SignupCode
    fieldsets = (
        (None, {
            'fields': ('code', 'ipaddr', 'created_at')
        }),
    )
    readonly_fields = ('code', 'ipaddr', 'created_at')

    def has_add_permission(self, request):
        return False


class PasswordResetCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'user', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('user', 'code')

    def has_add_permission(self, request):
        return False


class PasswordResetCodeInline(admin.TabularInline):
    model = PasswordResetCode
    fieldsets = (
        (None, {
            'fields': ('code', 'created_at')
        }),
    )
    readonly_fields = ('code', 'created_at')

    def has_add_permission(self, request):
        return False


class EmailUserAdmin(UserAdmin):

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal Info'), {'fields': ('username','faculty','macid','lable','score')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                        'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'is_staff', 'is_verified'),
        }),
    )
    form = EmailUserChangeForm
    add_form = EmailUserCreationForm
    inlines = [SignupCodeInline, PasswordResetCodeInline]
    list_display = ('email', 'is_verified', 
                    'username', 'is_staff')
    search_fields = ('username', 'email')
    ordering = ('email',)


admin.site.register(MyUser, EmailUserAdmin)
admin.site.register(SignupCode, SignupCodeAdmin)
admin.site.register(PasswordResetCode, PasswordResetCodeAdmin)
