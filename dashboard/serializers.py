from rest_framework import serializers

class ChannelSerializer(serializers.Serializer):
    _id = serializers.CharField()
    channel_name = serializers.CharField(max_length=255)
    description = serializers.CharField(allow_blank=True, required=False)
    location = serializers.CharField(max_length=255, required=False)
    privacy = serializers.CharField(max_length=50, required=False)
    sensor = serializers.ListField(child=serializers.DictField(), required=False)
    allow_API = serializers.CharField(max_length=50, required=False)
    API_KEY = serializers.CharField(max_length=255, required=False)
    user_id = serializers.CharField(max_length=50, required=False)
    date_created = serializers.CharField(allow_blank=True, required=False)
    date_modified = serializers.CharField(allow_blank=True, required=False)
    sensor_count = serializers.IntegerField(required=False, default=0)
