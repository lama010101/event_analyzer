import os
import json
import requests
from datetime import datetime
from typing import Optional, List, Dict, Any

class SupabaseManager:
    """Manages Supabase database operations for historical image analysis results"""
    
    def __init__(self):
        # Set Supabase credentials directly since environment variables might not persist
        self.supabase_url = "https://jghesmrwhegaotbztrhr.supabase.co"
        self.supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpnaGVzbXJ3aGVnYW90Ynp0cmhyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ0MzAwMDEsImV4cCI6MjA2MDAwNjAwMX0.C-zSGAiZAIbvKh9vNb2_s3DHogSzSKImLkRbjr_h5xI"
        
        # Try environment variables first, then fall back to hardcoded
        env_url = os.getenv('VITE_SUPABASE_URL') or os.getenv('NEXT_PUBLIC_SUPABASE_URL')
        env_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('VITE_SUPABASE_ANON_KEY') or os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY')
        
        if env_url:
            self.supabase_url = env_url
        if env_key:
            self.supabase_key = env_key
        
        self.headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
        
        self.base_url = f"{self.supabase_url}/rest/v1"
        self.table_name = "ai-guess"
        
        print(f"Supabase initialized with URL: {self.supabase_url}")
        print(f"Using key: {self.supabase_key[:20]}...")
        
    def ensure_table_columns(self):
        """Ensure the ai-guess table has all necessary columns"""
        # Note: In a real scenario, you would run these SQL commands in Supabase dashboard
        # or use the admin API. For now, we'll assume the table exists and add columns as needed
        print("Note: Ensure the 'ai-guess' table has the following columns:")
        print("- id (primary key)")
        print("- image_name (text)")
        print("- title (text)")
        print("- event (text)")
        print("- description (text)")
        print("- location_name (text)")
        print("- gps_lat (decimal)")
        print("- gps_lon (decimal)")
        print("- year (integer)")
        print("- exact_date (text)")
        print("- ai_generated_probability (integer)")
        print("- ai_analysis (text)")
        print("- extracted_text (text)")
        print("- visual_elements (text)")
        print("- confidence_year (integer)")
        print("- confidence_location (integer)")
        print("- confidence_event (integer)")
        print("- confidence_exact_date (integer)")
        print("- wikipedia_search_url (text)")
        print("- wikipedia_direct_url (text)")
        print("- image_url (text)")
        print("- prompt (text)")
        print("- celebrity (boolean, default false)")
        print("- celebrity_name (text)")
        print("- raw_result (jsonb)")
        print("- created_at (timestamp with time zone, default now())")
    
    def save_analysis_result(self, result: Dict[Any, Any], image_name: str, image_url: str = None) -> Optional[int]:
        """Save analysis result to Supabase"""
        try:
            # Extract GPS coordinates
            gps_lat, gps_lon = None, None
            if result.get('gps') and len(result['gps']) == 2:
                gps_lat, gps_lon = result['gps']
            
            # Extract confidence scores
            confidence = result.get('confidence', {})
            
            # Extract Wikipedia URLs
            wikipedia = result.get('wikipedia', {})
            
            # Prepare data for insertion
            data = {
                'image_name': image_name,
                'title': result.get('title'),
                'event': result.get('event'),
                'description': result.get('description'),
                'location_name': result.get('location_name'),
                'gps_lat': gps_lat,
                'gps_lon': gps_lon,
                'year': result.get('year'),
                'exact_date': result.get('exact_date'),
                'ai_generated_probability': result.get('ai_generated_probability'),
                'ai_analysis': result.get('ai_analysis'),
                'extracted_text': result.get('extracted_text'),
                'visual_elements': json.dumps(result.get('visual_elements')) if result.get('visual_elements') else None,
                'confidence_year': confidence.get('year'),
                'confidence_location': confidence.get('location'),
                'confidence_event': confidence.get('event'),
                'confidence_exact_date': confidence.get('exact_date'),
                'wikipedia_search_url': wikipedia.get('search_url'),
                'wikipedia_direct_url': wikipedia.get('direct_url'),
                'image_url': image_url,
                'prompt': result.get('prompt'),
                'celebrity': result.get('celebrity', False),
                'celebrity_name': result.get('celebrity_name'),
                'raw_result': result,
                'created_at': datetime.now().isoformat()
            }
            
            # Make POST request to Supabase with detailed logging
            print(f"Attempting to save to Supabase table: {self.table_name}")
            print(f"URL: {self.base_url}/{self.table_name}")
            print(f"Data keys: {list(data.keys())}")
            
            response = requests.post(
                f"{self.base_url}/{self.table_name}",
                headers=self.headers,
                json=data
            )
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            if response.status_code in [200, 201]:
                result_data = response.json()
                print(f"Success! Inserted data: {result_data}")
                if result_data and len(result_data) > 0:
                    return result_data[0].get('id')
                return None
            else:
                print(f"Error saving to Supabase: {response.status_code}")
                print(f"Response text: {response.text}")
                print(f"Request headers: {self.headers}")
                # Try to parse error details
                try:
                    error_detail = response.json()
                    print(f"Error details: {error_detail}")
                except:
                    pass
                return None
                
        except Exception as e:
            print(f"Error saving to Supabase: {str(e)}")
            return None
    
    def get_analysis_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent analysis history from Supabase"""
        try:
            response = requests.get(
                f"{self.base_url}/{self.table_name}",
                headers=self.headers,
                params={
                    'select': 'id,image_name,title,event,location_name,year,exact_date,ai_generated_probability,created_at',
                    'order': 'created_at.desc',
                    'limit': limit
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error getting history: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"Error getting history from Supabase: {str(e)}")
            return []
    
    def search_analysis_results(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search analysis results by event, title, or location"""
        try:
            # Supabase text search using ilike (case-insensitive LIKE)
            # Search across multiple columns using 'or' operator
            params = {
                'select': 'id,image_name,title,event,location_name,year,exact_date,ai_generated_probability,created_at',
                'or': f'(title.ilike.*{query}*,event.ilike.*{query}*,location_name.ilike.*{query}*)',
                'order': 'created_at.desc',
                'limit': str(limit)
            }
            
            response = requests.get(
                f"{self.base_url}/{self.table_name}",
                headers=self.headers,
                params=params
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error searching: {response.status_code} - {response.text}")
                # Fallback: try simpler search on title only
                fallback_params = {
                    'select': 'id,image_name,title,event,location_name,year,exact_date,ai_generated_probability,created_at',
                    'title': f'ilike.*{query}*',
                    'order': 'created_at.desc',
                    'limit': str(limit)
                }
                
                fallback_response = requests.get(
                    f"{self.base_url}/{self.table_name}",
                    headers=self.headers,
                    params=fallback_params
                )
                
                if fallback_response.status_code == 200:
                    return fallback_response.json()
                else:
                    return []
                
        except Exception as e:
            print(f"Error searching Supabase: {str(e)}")
            return []
    
    def get_analysis_by_id(self, analysis_id: int) -> Optional[Dict[str, Any]]:
        """Get full analysis result by ID from Supabase"""
        try:
            response = requests.get(
                f"{self.base_url}/{self.table_name}",
                headers=self.headers,
                params={
                    'id': f'eq.{analysis_id}',
                    'select': 'raw_result'
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    return data[0].get('raw_result')
                return None
            else:
                print(f"Error getting analysis by ID: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error getting analysis by ID from Supabase: {str(e)}")
            return None
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics from Supabase"""
        try:
            # Get total count
            count_response = requests.get(
                f"{self.base_url}/{self.table_name}",
                headers={**self.headers, 'Prefer': 'count=exact'},
                params={'select': 'id'}
            )
            
            total_records = 0
            if count_response.status_code == 200:
                # Extract count from headers
                total_records = int(count_response.headers.get('Content-Range', '0-0/0').split('/')[-1])
            
            # Get records by year
            year_response = requests.get(
                f"{self.base_url}/{self.table_name}",
                headers=self.headers,
                params={
                    'select': 'year',
                    'year': 'not.is.null'
                }
            )
            
            records_by_year = {}
            if year_response.status_code == 200:
                year_data = year_response.json()
                year_counts = {}
                for record in year_data:
                    year = record.get('year')
                    if year:
                        year_counts[year] = year_counts.get(year, 0) + 1
                
                # Sort by year and limit to top 10
                sorted_years = sorted(year_counts.items(), key=lambda x: x[0], reverse=True)[:10]
                records_by_year = dict(sorted_years)
            
            # Get AI generated count
            ai_response = requests.get(
                f"{self.base_url}/{self.table_name}",
                headers={**self.headers, 'Prefer': 'count=exact'},
                params={
                    'select': 'id',
                    'ai_generated_probability': 'gt.70'
                }
            )
            
            ai_generated_count = 0
            if ai_response.status_code == 200:
                ai_generated_count = int(ai_response.headers.get('Content-Range', '0-0/0').split('/')[-1])
            
            return {
                'database_type': 'Supabase',
                'total_records': total_records,
                'records_by_year': records_by_year,
                'likely_ai_generated': ai_generated_count
            }
            
        except Exception as e:
            print(f"Error getting Supabase stats: {str(e)}")
            return {
                'database_type': 'Supabase',
                'total_records': 0,
                'records_by_year': {},
                'likely_ai_generated': 0
            }