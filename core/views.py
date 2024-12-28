import subprocess
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from django.views.decorators.gzip import gzip_page
from django.core.cache import cache
import os
import time

class TerminalLogView(TemplateView):
    template_name = "pages/terminal_logs.html"

@require_http_methods(["GET"])
@gzip_page
def get_terminal_logs(request):
    try:
        # Use absolute path
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_file = os.path.join(base_dir, 'logs', 'django.log')
        
        if not os.path.exists(log_file):
            return HttpResponse(
                f"Log file not found at {log_file}. "
                "Start server with: python manage.py runserver 2>&1 | tee logs/django.log",
                content_type='text/plain',
                status=404
            )
        
        # Get file stats
        stats = os.stat(log_file)
        current_mtime = stats.st_mtime
        current_size = stats.st_size
        
        # Check if we have a cached version
        cache_key = f'log_content_{current_mtime}_{current_size}'
        cached_content = cache.get(cache_key)
        
        if cached_content:
            return HttpResponse(cached_content, content_type='text/plain')
        
        # Read the file if no cache or modified
        try:
            with open(log_file, 'r') as f:
                content = f.read()
                
            # Cache for 1 second
            cache.set(cache_key, content, 1)
            
            return HttpResponse(content, content_type='text/plain')
        except (IOError, OSError) as e:
            return HttpResponse(
                f"Error reading log file: {str(e)}",
                content_type='text/plain',
                status=500
            )
            
    except Exception as e:
        return HttpResponse(
            f"Unexpected error: {str(e)}",
            content_type='text/plain',
            status=500
        )