from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Document, DocumentVersion, FileUpload, ActivityLog


class UserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='profile.role', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role']


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'role', 'created_at']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, default='editor')
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role']
    
    def create(self, validated_data):
        role = validated_data.pop('role', 'editor')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        UserProfile.objects.create(user=user, role=role)
        return user


class DocumentSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    collaborators = UserSerializer(many=True, read_only=True)
    collaborator_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Document
        fields = ['id', 'title', 'content', 'owner', 'collaborators', 
                  'collaborator_ids', 'version', 'created_at', 'updated_at']
        read_only_fields = ['owner', 'version']
    
    def create(self, validated_data):
        collaborator_ids = validated_data.pop('collaborator_ids', [])
        document = Document.objects.create(**validated_data)
        if collaborator_ids:
            document.collaborators.set(User.objects.filter(id__in=collaborator_ids))
        return document


class DocumentVersionSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = DocumentVersion
        fields = ['id', 'content', 'version_number', 'created_by', 'created_at']


class FileUploadSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)
    
    class Meta:
        model = FileUpload
        fields = ['id', 'file_name', 'file_url', 'file_size', 'uploaded_by', 'uploaded_at']


class ActivityLogSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    document_title = serializers.CharField(source='document.title', read_only=True)
    
    class Meta:
        model = ActivityLog
        fields = ['id', 'user', 'document', 'document_title', 'action', 'description', 'timestamp']
