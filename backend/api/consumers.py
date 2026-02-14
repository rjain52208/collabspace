import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Document, DocumentEdit, ActivityLog
import time


class DashboardConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for dashboard real-time updates"""
    
    async def connect(self):
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Join personal dashboard group
        self.dashboard_group = f'dashboard_{self.user.id}'
        await self.channel_layer.group_add(
            self.dashboard_group,
            self.channel_name
        )
        
        # Join global documents group
        await self.channel_layer.group_add(
            'documents_global',
            self.channel_name
        )
        
        await self.accept()
        print(f'Dashboard WebSocket connected for user {self.user.username}')
    
    async def disconnect(self, close_code):
        if hasattr(self, 'dashboard_group'):
            await self.channel_layer.group_discard(
                self.dashboard_group,
                self.channel_name
            )
        await self.channel_layer.group_discard(
            'documents_global',
            self.channel_name
        )
    
    # Event handlers
    async def document_created(self, event):
        await self.send(text_data=json.dumps({
            'type': 'document_created',
            'document_id': event['document_id'],
            'title': event['title']
        }))
    
    async def document_shared(self, event):
        await self.send(text_data=json.dumps({
            'type': 'document_shared',
            'document_id': event['document_id'],
            'title': event['title']
        }))


class DocumentConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time document collaboration"""
    
    async def connect(self):
        self.document_id = self.scope['url_route']['kwargs']['document_id']
        self.room_group_name = f'document_{self.document_id}'
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Check if user has access to document
        has_access = await self.check_document_access()
        if not has_access:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Notify others about new user
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user': self.user.username,
                'user_id': self.user.id
            }
        )
    
    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            # Notify others about user leaving
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_left',
                    'user': self.user.username,
                    'user_id': self.user.id
                }
            )
            
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'edit':
                await self.handle_edit(data)
            elif message_type == 'cursor':
                await self.handle_cursor_position(data)
            elif message_type == 'lock':
                await self.handle_lock(data)
        except Exception as e:
            print(f"Error in receive: {e}")
            import traceback
            traceback.print_exc()
    
    async def handle_edit(self, data):
        """Handle document edit with conflict resolution"""
        try:
            operation = data.get('operation')  # 'insert', 'delete', 'replace'
            position = data.get('position')
            content = data.get('content', '')
            version = data.get('version')
            timestamp = time.time()
            
            # Save edit to database for conflict resolution
            await self.save_edit(operation, position, content)
            
            # Get current document version
            current_version = await self.get_document_version()
            
            # Check for conflicts
            if version and version < current_version:
                # Conflict detected - apply operational transformation
                transformed_data = await self.resolve_conflict(data)
                data.update(transformed_data)
            
            # Update document
            await self.update_document(data)
            
            # Broadcast to all users in the room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'document_edit',
                    'user': self.user.username,
                    'user_id': self.user.id,
                    'operation': operation,
                    'position': position,
                    'content': content,
                    'timestamp': timestamp,
                    'version': current_version + 1
                }
            )
        except Exception as e:
            print(f"Error in handle_edit: {e}")
            import traceback
            traceback.print_exc()
    
    async def handle_cursor_position(self, data):
        """Broadcast cursor position to other users"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'cursor_update',
                'user': self.user.username,
                'user_id': self.user.id,
                'position': data.get('position')
            }
        )
    
    async def handle_lock(self, data):
        """Handle document locking mechanism"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'lock_update',
                'user': self.user.username,
                'user_id': self.user.id,
                'locked': data.get('locked', False),
                'section': data.get('section')
            }
        )
    
    # WebSocket message handlers
    async def user_joined(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user': event['user'],
            'user_id': event['user_id']
        }))
    
    async def user_left(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user': event['user'],
            'user_id': event['user_id']
        }))
    
    async def document_edit(self, event):
        # Don't send back to the same user
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'edit',
                'user': event['user'],
                'operation': event['operation'],
                'position': event['position'],
                'content': event['content'],
                'timestamp': event['timestamp'],
                'version': event['version']
            }))
    
    async def cursor_update(self, event):
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'cursor',
                'user': event['user'],
                'position': event['position']
            }))
    
    async def lock_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'lock',
            'user': event['user'],
            'locked': event['locked'],
            'section': event['section']
        }))
    
    # Database operations
    @database_sync_to_async
    def check_document_access(self):
        """Check if user has access to document"""
        try:
            document = Document.objects.get(id=self.document_id)
            return document.owner == self.user or self.user in document.collaborators.all()
        except Document.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_edit(self, operation, position, content):
        """Save edit to database"""
        try:
            document = Document.objects.get(id=self.document_id)
            DocumentEdit.objects.create(
                document=document,
                user=self.user,
                operation=operation,
                position=position,
                content=content,
                applied=True
            )
        except Document.DoesNotExist:
            pass
    
    @database_sync_to_async
    def get_document_version(self):
        """Get current document version"""
        try:
            document = Document.objects.get(id=self.document_id)
            return document.version
        except Document.DoesNotExist:
            return 0
    
    @database_sync_to_async
    def update_document(self, data):
        """Update document content"""
        try:
            document = Document.objects.get(id=self.document_id)
            operation = data['operation']
            position = data['position']
            content = data['content']
            
            # Simple operational transformation
            if operation == 'insert':
                document.content = (
                    document.content[:position] + 
                    content + 
                    document.content[position:]
                )
            elif operation == 'delete':
                length = data.get('length', 1)
                document.content = (
                    document.content[:position] + 
                    document.content[position + length:]
                )
            elif operation == 'replace':
                length = data.get('length', 1)
                document.content = (
                    document.content[:position] + 
                    content + 
                    document.content[position + length:]
                )
            
            document.version += 1
            document.save()
        except Document.DoesNotExist:
            pass
    
    @database_sync_to_async
    def resolve_conflict(self, data):
        """Apply operational transformation for conflict resolution"""
        try:
            document = Document.objects.get(id=self.document_id)
            # Get timestamp from data - it's already a number (time.time())
            data_timestamp = data.get('timestamp', 0)
            
            # Get edits that happened after the user's edit (using numeric timestamp)
            newer_edits = DocumentEdit.objects.filter(
                document=document,
                applied=True
            ).order_by('timestamp')
            
            # Transform position based on newer edits
            position = data['position']
            for edit in newer_edits:
                # Convert edit timestamp to float for comparison if it's a string
                edit_timestamp = float(edit.timestamp.timestamp()) if hasattr(edit.timestamp, 'timestamp') else float(edit.timestamp)
                
                if edit_timestamp > data_timestamp:
                    if edit.operation == 'insert' and edit.position <= position:
                        position += len(edit.content)
                    elif edit.operation == 'delete' and edit.position < position:
                        position -= 1
            
            return {'position': position}
        except Document.DoesNotExist:
            return {}
        except Exception as e:
            print(f"Error in resolve_conflict: {e}")
            import traceback
            traceback.print_exc()
            return {}
