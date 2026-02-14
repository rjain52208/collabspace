from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('editor', 'Editor'),
        ('viewer', 'Viewer'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='editor')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"


class Document(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_documents')
    collaborators = models.ManyToManyField(User, related_name='shared_documents', blank=True)
    version = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return self.title


class DocumentVersion(models.Model):
    """Stores versions for conflict resolution"""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='versions')
    content = models.TextField()
    version_number = models.IntegerField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-version_number']
        unique_together = ['document', 'version_number']


class DocumentEdit(models.Model):
    """Operational Transformation tracking for conflict resolution"""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='edits')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    operation = models.CharField(max_length=20)  # 'insert', 'delete', 'replace'
    position = models.IntegerField()
    content = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    applied = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']


class FileUpload(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='files')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255)
    file_url = models.URLField()
    file_size = models.IntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.file_name} - {self.document.title}"


class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Created'),
        ('edit', 'Edited'),
        ('delete', 'Deleted'),
        ('share', 'Shared'),
        ('upload', 'Uploaded File'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='activities', null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp}"
