from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User
from django.db.models import Q
import boto3
from django.conf import settings

from .models import Document, DocumentVersion, FileUpload, ActivityLog, UserProfile
from .serializers import (
    DocumentSerializer, UserSerializer, RegisterSerializer,
    FileUploadSerializer, ActivityLogSerializer, DocumentVersionSerializer
)
from .permissions import IsEditorOrAdmin, IsDocumentOwnerOrCollaborator


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """User registration endpoint"""
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            'user': UserSerializer(user).data,
            'message': 'User created successfully'
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    """Get current user info"""
    return Response(UserSerializer(request.user).data)


class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated, IsEditorOrAdmin]
    
    def get_queryset(self):
        """Get documents owned by or shared with the user"""
        return Document.objects.filter(
            Q(owner=self.request.user) | Q(collaborators=self.request.user)
        ).distinct()
    
    def perform_create(self, serializer):
        """Create document and log activity"""
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        document = serializer.save(owner=self.request.user)
        
        # Auto-share with all users for simplicity
        from django.contrib.auth.models import User
        all_users = User.objects.exclude(id=self.request.user.id)
        document.collaborators.set(all_users)
        
        ActivityLog.objects.create(
            user=self.request.user,
            document=document,
            action='create',
            description=f'Created document "{document.title}"'
        )
        
        # Create initial version
        DocumentVersion.objects.create(
            document=document,
            content=document.content,
            version_number=1,
            created_by=self.request.user
        )
        
        # Broadcast to all dashboards
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'documents_global',
            {
                'type': 'document_created',
                'document_id': document.id,
                'title': document.title
            }
        )
    
    def perform_update(self, serializer):
        """Update document and create new version"""
        document = serializer.save()
        document.version += 1
        document.save()
        
        # Create version snapshot
        DocumentVersion.objects.create(
            document=document,
            content=document.content,
            version_number=document.version,
            created_by=self.request.user
        )
        
        ActivityLog.objects.create(
            user=self.request.user,
            document=document,
            action='edit',
            description=f'Edited document "{document.title}"'
        )
    
    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """Share document with collaborators"""
        document = self.get_object()
        if document.owner != request.user:
            return Response(
                {'error': 'Only owner can share document'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_ids = request.data.get('user_ids', [])
        users = User.objects.filter(id__in=user_ids)
        document.collaborators.add(*users)
        
        ActivityLog.objects.create(
            user=request.user,
            document=document,
            action='share',
            description=f'Shared document with {len(users)} users'
        )
        
        return Response({'message': 'Document shared successfully'})
    
    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        """Get document version history"""
        document = self.get_object()
        versions = document.versions.all()[:10]  # Last 10 versions
        serializer = DocumentVersionSerializer(versions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def upload_file(self, request, pk=None):
        """Upload file to S3 and attach to document"""
        document = self.get_object()
        file = request.FILES.get('file')
        
        if not file:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Upload to S3 if configured, otherwise return error
        if not settings.AWS_ACCESS_KEY_ID:
            return Response(
                {'error': 'AWS S3 not configured. Please set AWS credentials.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )
            
            file_key = f'documents/{document.id}/{file.name}'
            s3_client.upload_fileobj(
                file,
                settings.AWS_STORAGE_BUCKET_NAME,
                file_key
            )
            
            file_url = f'https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{file_key}'
            
            file_upload = FileUpload.objects.create(
                document=document,
                uploaded_by=request.user,
                file_name=file.name,
                file_url=file_url,
                file_size=file.size
            )
            
            ActivityLog.objects.create(
                user=request.user,
                document=document,
                action='upload',
                description=f'Uploaded file "{file.name}"'
            )
            
            return Response(FileUploadSerializer(file_upload).data)
            
        except Exception as e:
            return Response(
                {'error': f'Upload failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get activity logs for documents user has access to"""
        user_documents = Document.objects.filter(
            Q(owner=self.request.user) | Q(collaborators=self.request.user)
        )
        return ActivityLog.objects.filter(
            Q(user=self.request.user) | Q(document__in=user_documents)
        ).distinct()[:50]  # Last 50 activities
