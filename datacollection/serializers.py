from rest_framework import serializers


class collectionLogSerializer(serializers.Serializer):
    """
    Don't require email to be unique so visitor can signup multiple times,
    if misplace verification email.  Handle in view.
    """
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(max_length=128)
    username = serializers.CharField(max_length=30, default='',
        required=False)
    faculty = serializers.CharField(max_length=30, default='',
        required=False)

    # last_name = serializers.CharField(max_length=30, default='',
    #     required=False)


class fpDataSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(max_length=128)

class taskitemSerializer(serializers.Serializer):
    macid = serializers.CharField(max_length=30, default='', 
        required=False)

class taskAssignSerializer(serializers.Serializer):
    taskid = serializers.IntegerField(max_value=None,
        min_value=None)
    macid = serializers.CharField(max_length=30, default='',
        required=False)

