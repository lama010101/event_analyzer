"""
Main entry point for Vercel deployment
Simple Flask app that redirects to the full Streamlit application
"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

def handler(request, response):
    """Vercel serverless function handler"""
    try:
        response.status_code = 200
        response.headers['Content-Type'] = 'text/html'
        
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Historical Image Analysis</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f0f2f6; }
                .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
                .button { background: #ff6b6b; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px; }
                .description { margin: 20px 0; color: #666; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📸 Historical Image Analysis AI</h1>
                <p class="description">
                    Advanced AI-powered platform that analyzes historical images to identify events, 
                    dates, locations, celebrities, and comprehensive metadata using OpenAI GPT-4o Vision.
                </p>
                <h3>Features:</h3>
                <ul style="text-align: left; max-width: 400px; margin: 0 auto;">
                    <li>Multiple image upload support</li>
                    <li>Celebrity detection with names</li>
                    <li>Exact date identification</li>
                    <li>AI-generation probability assessment</li>
                    <li>Wikipedia integration</li>
                    <li>Supabase database storage</li>
                    <li>Firebase image optimization</li>
                </ul>
                <p style="margin-top: 30px;">
                    <strong>Note:</strong> This is a Streamlit application that requires a full server environment. 
                    For complete functionality, please run the application on Replit or a compatible hosting platform.
                </p>
                <a href="https://replit.com" class="button">Run on Replit</a>
                <p style="margin-top: 20px; font-size: 12px; color: #999;">
                    Contact the developer for deployment assistance or API access.
                </p>
            </div>
        </body>
        </html>
        """
        
    except Exception as e:
        response.status_code = 500
        return f"""
        <html><body>
        <h1>Error</h1>
        <p>Application error: {str(e)}</p>
        <p>Please contact support.</p>
        </body></html>
        """