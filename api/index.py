from http.server import HTTPServer, SimpleHTTPRequestHandler
import subprocess
import os
import sys

# Add the parent directory to the path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def handler(request, response):
    """Vercel serverless function handler"""
    try:
        # Start streamlit in the background
        os.system("streamlit run ../app.py --server.headless=true --server.port=8501 &")
        
        response.status_code = 200
        response.headers['Content-Type'] = 'text/html'
        
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Historical Image Analysis</title>
            <meta http-equiv="refresh" content="0; url=http://localhost:8501">
        </head>
        <body>
            <p>Redirecting to Streamlit app...</p>
            <script>
                window.location.href = 'http://localhost:8501';
            </script>
        </body>
        </html>
        """
        
    except Exception as e:
        response.status_code = 500
        return f"Error: {str(e)}"