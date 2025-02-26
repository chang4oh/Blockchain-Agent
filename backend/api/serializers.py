from rest_framework import serializers
from .models import UserSettings, TradeLog
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')

class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')

class TradeLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradeLog
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at', 'pnl', 'pnl_percentage')

    def validate(self, data):
        if data.get('exit_price') and data.get('status') != 'CLOSED':
            raise serializers.ValidationError("Trade must be closed if exit price is provided")
        return data 