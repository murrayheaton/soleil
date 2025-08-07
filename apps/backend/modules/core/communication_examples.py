"""
Module Communication Examples

This file demonstrates how modules should communicate with each other
using the EventBus and APIGateway.
"""

from modules.core import get_event_bus, get_api_gateway, events, Event
import asyncio
import logging

logger = logging.getLogger(__name__)


# Example 1: Auth → Drive Communication (OAuth Tokens)
async def auth_to_drive_oauth_example():
    """
    When auth module refreshes OAuth tokens, it notifies the drive module
    so it can update its credentials.
    """
    event_bus = get_event_bus()
    
    # In Drive Module - Subscribe to auth events
    async def handle_token_refresh(event: Event):
        user_id = event.data.get('user_id')
        new_token = event.data.get('access_token')
        refresh_token = event.data.get('refresh_token')
        
        logger.info(f"Drive module received new token for user {user_id}")
        # Update drive service credentials
        # drive_service.update_credentials(user_id, new_token, refresh_token)
    
    # Drive module subscribes during initialization
    event_bus.subscribe(
        events.AUTH_TOKEN_REFRESHED,
        handle_token_refresh,
        target_module='drive'
    )
    
    # In Auth Module - Publish event after token refresh
    await event_bus.publish(
        event_type=events.AUTH_TOKEN_REFRESHED,
        data={
            'user_id': 'user123',
            'access_token': 'new_access_token',
            'refresh_token': 'new_refresh_token',
            'expires_in': 3600
        },
        source_module='auth'
    )


# Example 2: Content → Sync Communication (File Updates)
async def content_to_sync_file_update_example():
    """
    When content module parses a new file, it notifies sync module
    to update all connected clients.
    """
    event_bus = get_event_bus()
    
    # In Sync Module - Subscribe to content events
    async def handle_content_update(event: Event):
        file_info = event.data.get('file_info')
        action = event.data.get('action')
        
        logger.info(f"Sync module broadcasting {action} for {file_info['name']}")
        # Broadcast to WebSocket clients
        # await websocket_manager.broadcast({
        #     'type': 'content_update',
        #     'action': action,
        #     'file': file_info
        # })
    
    # Sync module subscribes during initialization
    event_bus.subscribe(
        events.CONTENT_UPDATED,
        handle_content_update,
        target_module='sync'
    )
    
    # In Content Module - Publish event after parsing
    await event_bus.publish(
        event_type=events.CONTENT_UPDATED,
        data={
            'action': 'parsed',
            'file_info': {
                'id': 'file456',
                'name': 'Song Title - Bb.pdf',
                'instruments': ['trumpet', 'saxophone'],
                'parsed_data': {
                    'title': 'Song Title',
                    'key': 'Bb',
                    'tempo': 120
                }
            }
        },
        source_module='content'
    )


# Example 3: Sync → Frontend Communication (WebSocket Events)
async def sync_to_frontend_websocket_example():
    """
    Sync module sends real-time updates to frontend clients via WebSocket.
    """
    event_bus = get_event_bus()
    
    # This would be in the WebSocket handler
    async def broadcast_sync_progress(event: Event):
        progress_data = event.data
        # In real implementation:
        # await websocket.send_json({
        #     'type': 'sync_progress',
        #     'data': progress_data
        # })
        logger.info(f"Broadcasting sync progress: {progress_data['percent']}%")
    
    # Frontend WebSocket connection subscribes to sync events
    event_bus.subscribe(
        events.SYNC_PROGRESS,
        broadcast_sync_progress,
        target_module='frontend'
    )
    
    # Sync module publishes progress updates
    for percent in [0, 25, 50, 75, 100]:
        await event_bus.publish(
            event_type=events.SYNC_PROGRESS,
            data={
                'percent': percent,
                'current_file': f'file_{percent}.pdf',
                'total_files': 100,
                'processed_files': percent
            },
            source_module='sync'
        )
        await asyncio.sleep(0.1)  # Simulate work


# Example 4: Using Service Discovery
def service_discovery_example():
    """
    Demonstrate how modules can discover and use services from other modules.
    """
    api_gateway = get_api_gateway()
    
    # Auth module registers its services
    from modules.auth.services import AuthService, JWTService
    
    auth_service = AuthService()
    jwt_service = JWTService()
    
    api_gateway.register_module(
        name='auth',
        router=None,  # Router would be provided in real implementation
        version='1.0.0',
        services={
            'auth': auth_service,
            'jwt': jwt_service
        }
    )
    
    # Drive module can now get auth services
    try:
        # Get JWT service from auth module
        jwt_service = api_gateway.get_module_service('auth', 'jwt')
        
        # Use the service
        token = jwt_service.create_access_token({'user_id': 'user123'})
        logger.info(f"Created token using auth module's JWT service")
        
    except ValueError as e:
        logger.error(f"Failed to get service: {e}")


# Example 5: Module Health Checks
async def health_check_example():
    """
    Demonstrate module health check implementation.
    """
    api_gateway = get_api_gateway()
    
    # Define health check for drive module
    async def drive_health_check():
        # Check drive service status
        try:
            # Check database connection
            # db_status = await check_db_connection()
            
            # Check Google API availability
            # google_status = await check_google_api()
            
            return {
                'database': 'healthy',
                'google_api': 'healthy',
                'cache_size': '45MB',
                'active_connections': 12
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    # Register module with health check
    api_gateway.register_module(
        name='drive',
        router=None,  # Router would be provided
        version='1.0.0',
        health_check=drive_health_check
    )
    
    # Check module health
    health_result = await api_gateway.check_module_health('drive')
    logger.info(f"Drive module health: {health_result}")
    
    # Check all modules
    all_health = await api_gateway.check_all_health()
    logger.info(f"All modules health: {all_health}")


# Example 6: Error Handling and Recovery
async def error_handling_example():
    """
    Demonstrate proper error handling in module communication.
    """
    event_bus = get_event_bus()
    
    # Subscribe to system error events
    async def handle_system_error(event: Event):
        error_data = event.data
        module = error_data.get('module')
        error_type = error_data.get('error_type')
        
        logger.error(f"System error from {module}: {error_type}")
        
        # Take recovery action based on error type
        if error_type == 'rate_limit':
            # Implement backoff strategy
            logger.info("Implementing rate limit backoff")
        elif error_type == 'auth_failure':
            # Trigger re-authentication
            logger.info("Triggering re-authentication")
    
    event_bus.subscribe(
        events.SYSTEM_ERROR,
        handle_system_error,
        target_module='core'
    )
    
    # Module publishes error event
    await event_bus.publish(
        event_type=events.SYSTEM_ERROR,
        data={
            'module': 'drive',
            'error_type': 'rate_limit',
            'message': 'Google Drive API rate limit exceeded',
            'retry_after': 60
        },
        source_module='drive'
    )


# Main function to run all examples
async def main():
    """Run all communication examples."""
    logger.info("Running module communication examples...")
    
    # Run examples
    await auth_to_drive_oauth_example()
    await content_to_sync_file_update_example()
    await sync_to_frontend_websocket_example()
    service_discovery_example()
    await health_check_example()
    await error_handling_example()
    
    logger.info("All examples completed!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())