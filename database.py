import os
import json
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
from supabase_db import SupabaseManager

# Try to import psycopg2, fall back to None if not available
try:
    import psycopg2
except ImportError:
    psycopg2 = None

class DatabaseManager:
    """Manages database operations for historical image analysis results"""
    
    def __init__(self):
        self.db_type = self._detect_database_type()
        self.init_database()
    
    def _detect_database_type(self) -> str:
        """Detect which database to use based on environment"""
        # Always use Supabase as primary choice
        try:
            # Test if we can initialize Supabase
            test_supabase = SupabaseManager()
            return 'supabase'
        except Exception as e:
            print(f"Supabase not available: {str(e)}")
            # Check for PostgreSQL
            if os.getenv('DATABASE_URL') and psycopg2 is not None:
                return 'postgresql'
            else:
                return 'sqlite'
    
    def init_database(self):
        """Initialize database with required tables"""
        if self.db_type == 'supabase':
            self.supabase = SupabaseManager()
            self.supabase.ensure_table_columns()
        elif self.db_type == 'postgresql':
            self._init_postgresql()
        else:
            self._init_sqlite()
    
    def _init_postgresql(self):
        """Initialize PostgreSQL database"""
        if psycopg2 is None:
            print("psycopg2 not available, falling back to SQLite")
            self.db_type = 'sqlite'
            self._init_sqlite()
            return
            
        try:
            conn = psycopg2.connect(os.getenv('DATABASE_URL'))
            cursor = conn.cursor()
            
            # Create table for analysis results
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id SERIAL PRIMARY KEY,
                    image_name VARCHAR(255),
                    title VARCHAR(500),
                    event VARCHAR(500),
                    description TEXT,
                    location_name VARCHAR(255),
                    gps_lat DECIMAL(10, 8),
                    gps_lon DECIMAL(11, 8),
                    year INTEGER,
                    exact_date VARCHAR(20),
                    ai_generated_probability INTEGER,
                    ai_analysis TEXT,
                    extracted_text TEXT,
                    visual_elements TEXT,
                    confidence_year INTEGER,
                    confidence_location INTEGER,
                    confidence_event INTEGER,
                    confidence_exact_date INTEGER,
                    wikipedia_search_url TEXT,
                    wikipedia_direct_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    raw_result JSONB
                )
            """)
            
            conn.commit()
            conn.close()
            print("PostgreSQL database initialized successfully")
            
        except Exception as e:
            print(f"Error initializing PostgreSQL: {str(e)}")
            print("Falling back to SQLite")
            self.db_type = 'sqlite'
            self._init_sqlite()
    
    def _init_sqlite(self):
        """Initialize SQLite database as fallback"""
        try:
            conn = sqlite3.connect('historical_analysis.db')
            cursor = conn.cursor()
            
            # Create table for analysis results
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_name TEXT,
                    title TEXT,
                    event TEXT,
                    description TEXT,
                    location_name TEXT,
                    gps_lat REAL,
                    gps_lon REAL,
                    year INTEGER,
                    exact_date TEXT,
                    ai_generated_probability INTEGER,
                    ai_analysis TEXT,
                    extracted_text TEXT,
                    visual_elements TEXT,
                    confidence_year INTEGER,
                    confidence_location INTEGER,
                    confidence_event INTEGER,
                    confidence_exact_date INTEGER,
                    wikipedia_search_url TEXT,
                    wikipedia_direct_url TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    raw_result TEXT
                )
            """)
            
            conn.commit()
            conn.close()
            print("SQLite database initialized successfully")
            
        except Exception as e:
            print(f"Error initializing SQLite: {str(e)}")
    
    def save_analysis_result(self, result: Dict[Any, Any], image_name: str, image_url: str = None) -> Optional[int]:
        """Save analysis result to database"""
        try:
            if self.db_type == 'supabase':
                return self.supabase.save_analysis_result(result, image_name, image_url)
            elif self.db_type == 'postgresql':
                return self._save_to_postgresql(result, image_name)
            else:
                return self._save_to_sqlite(result, image_name)
        except Exception as e:
            print(f"Error saving to database: {str(e)}")
            return None
    
    def _save_to_postgresql(self, result: Dict[Any, Any], image_name: str) -> Optional[int]:
        """Save to PostgreSQL database"""
        if psycopg2 is None:
            return self._save_to_sqlite(result, image_name)
            
        try:
            conn = psycopg2.connect(os.getenv('DATABASE_URL'))
            cursor = conn.cursor()
            
            # Extract GPS coordinates
            gps_lat, gps_lon = None, None
            if result.get('gps') and len(result['gps']) == 2:
                gps_lat, gps_lon = result['gps']
            
            # Extract confidence scores
            confidence = result.get('confidence', {})
            
            # Extract Wikipedia URLs
            wikipedia = result.get('wikipedia', {})
            
            cursor.execute("""
                INSERT INTO analysis_results (
                    image_name, title, event, description, location_name,
                    gps_lat, gps_lon, year, exact_date, ai_generated_probability,
                    ai_analysis, extracted_text, visual_elements,
                    confidence_year, confidence_location, confidence_event, confidence_exact_date,
                    wikipedia_search_url, wikipedia_direct_url, raw_result
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                image_name,
                result.get('title'),
                result.get('event'),
                result.get('description'),
                result.get('location_name'),
                gps_lat,
                gps_lon,
                result.get('year'),
                result.get('exact_date'),
                result.get('ai_generated_probability'),
                result.get('ai_analysis'),
                result.get('extracted_text'),
                json.dumps(result.get('visual_elements')),
                confidence.get('year'),
                confidence.get('location'),
                confidence.get('event'),
                confidence.get('exact_date'),
                wikipedia.get('search_url'),
                wikipedia.get('direct_url'),
                json.dumps(result)
            ))
            
            record_id = cursor.fetchone()[0]
            conn.commit()
            conn.close()
            return record_id
            
        except Exception as e:
            print(f"Error saving to PostgreSQL: {str(e)}")
            return None
    
    def _save_to_sqlite(self, result: Dict[Any, Any], image_name: str) -> Optional[int]:
        """Save to SQLite database"""
        try:
            conn = sqlite3.connect('historical_analysis.db')
            cursor = conn.cursor()
            
            # Extract GPS coordinates
            gps_lat, gps_lon = None, None
            if result.get('gps') and len(result['gps']) == 2:
                gps_lat, gps_lon = result['gps']
            
            # Extract confidence scores
            confidence = result.get('confidence', {})
            
            # Extract Wikipedia URLs
            wikipedia = result.get('wikipedia', {})
            
            cursor.execute("""
                INSERT INTO analysis_results (
                    image_name, title, event, description, location_name,
                    gps_lat, gps_lon, year, exact_date, ai_generated_probability,
                    ai_analysis, extracted_text, visual_elements,
                    confidence_year, confidence_location, confidence_event, confidence_exact_date,
                    wikipedia_search_url, wikipedia_direct_url, created_at, raw_result
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                image_name,
                result.get('title'),
                result.get('event'),
                result.get('description'),
                result.get('location_name'),
                gps_lat,
                gps_lon,
                result.get('year'),
                result.get('exact_date'),
                result.get('ai_generated_probability'),
                result.get('ai_analysis'),
                result.get('extracted_text'),
                json.dumps(result.get('visual_elements')),
                confidence.get('year'),
                confidence.get('location'),
                confidence.get('event'),
                confidence.get('exact_date'),
                wikipedia.get('search_url'),
                wikipedia.get('direct_url'),
                datetime.now().isoformat(),
                json.dumps(result)
            ))
            
            record_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return record_id
            
        except Exception as e:
            print(f"Error saving to SQLite: {str(e)}")
            return None
    
    def get_analysis_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent analysis history"""
        try:
            if self.db_type == 'supabase':
                return self.supabase.get_analysis_history(limit)
            elif self.db_type == 'postgresql':
                return self._get_history_postgresql(limit)
            else:
                return self._get_history_sqlite(limit)
        except Exception as e:
            print(f"Error retrieving history: {str(e)}")
            return []
    
    def _get_history_postgresql(self, limit: int) -> List[Dict[str, Any]]:
        """Get history from PostgreSQL"""
        if psycopg2 is None:
            return self._get_history_sqlite(limit)
            
        try:
            conn = psycopg2.connect(os.getenv('DATABASE_URL'))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, image_name, title, event, location_name, year, exact_date,
                       ai_generated_probability, created_at
                FROM analysis_results
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'image_name': row[1],
                    'title': row[2],
                    'event': row[3],
                    'location_name': row[4],
                    'year': row[5],
                    'exact_date': row[6],
                    'ai_generated_probability': row[7],
                    'created_at': row[8]
                })
            
            conn.close()
            return results
            
        except Exception as e:
            print(f"Error getting PostgreSQL history: {str(e)}")
            return []
    
    def _get_history_sqlite(self, limit: int) -> List[Dict[str, Any]]:
        """Get history from SQLite"""
        try:
            conn = sqlite3.connect('historical_analysis.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, image_name, title, event, location_name, year, exact_date,
                       ai_generated_probability, created_at
                FROM analysis_results
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'image_name': row[1],
                    'title': row[2],
                    'event': row[3],
                    'location_name': row[4],
                    'year': row[5],
                    'exact_date': row[6],
                    'ai_generated_probability': row[7],
                    'created_at': row[8]
                })
            
            conn.close()
            return results
            
        except Exception as e:
            print(f"Error getting SQLite history: {str(e)}")
            return []
    
    def search_analysis_results(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search analysis results by event, title, or location"""
        try:
            if self.db_type == 'supabase':
                return self.supabase.search_analysis_results(query, limit)
            elif self.db_type == 'postgresql':
                return self._search_postgresql(query, limit)
            else:
                return self._search_sqlite(query, limit)
        except Exception as e:
            print(f"Error searching results: {str(e)}")
            return []
    
    def _search_postgresql(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search PostgreSQL database"""
        if psycopg2 is None:
            return self._search_sqlite(query, limit)
            
        try:
            conn = psycopg2.connect(os.getenv('DATABASE_URL'))
            cursor = conn.cursor()
            
            search_term = f"%{query}%"
            cursor.execute("""
                SELECT id, image_name, title, event, location_name, year, exact_date,
                       ai_generated_probability, created_at
                FROM analysis_results
                WHERE title ILIKE %s OR event ILIKE %s OR location_name ILIKE %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (search_term, search_term, search_term, limit))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'image_name': row[1],
                    'title': row[2],
                    'event': row[3],
                    'location_name': row[4],
                    'year': row[5],
                    'exact_date': row[6],
                    'ai_generated_probability': row[7],
                    'created_at': row[8]
                })
            
            conn.close()
            return results
            
        except Exception as e:
            print(f"Error searching PostgreSQL: {str(e)}")
            return []
    
    def _search_sqlite(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search SQLite database"""
        try:
            conn = sqlite3.connect('historical_analysis.db')
            cursor = conn.cursor()
            
            search_term = f"%{query}%"
            cursor.execute("""
                SELECT id, image_name, title, event, location_name, year, exact_date,
                       ai_generated_probability, created_at
                FROM analysis_results
                WHERE title LIKE ? OR event LIKE ? OR location_name LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (search_term, search_term, search_term, limit))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'image_name': row[1],
                    'title': row[2],
                    'event': row[3],
                    'location_name': row[4],
                    'year': row[5],
                    'exact_date': row[6],
                    'ai_generated_probability': row[7],
                    'created_at': row[8]
                })
            
            conn.close()
            return results
            
        except Exception as e:
            print(f"Error searching SQLite: {str(e)}")
            return []
    
    def get_analysis_by_id(self, analysis_id: int) -> Optional[Dict[str, Any]]:
        """Get full analysis result by ID"""
        try:
            if self.db_type == 'supabase':
                return self.supabase.get_analysis_by_id(analysis_id)
            elif self.db_type == 'postgresql':
                return self._get_by_id_postgresql(analysis_id)
            else:
                return self._get_by_id_sqlite(analysis_id)
        except Exception as e:
            print(f"Error retrieving analysis by ID: {str(e)}")
            return None
    
    def _get_by_id_postgresql(self, analysis_id: int) -> Optional[Dict[str, Any]]:
        """Get analysis by ID from PostgreSQL"""
        if psycopg2 is None:
            return self._get_by_id_sqlite(analysis_id)
            
        try:
            conn = psycopg2.connect(os.getenv('DATABASE_URL'))
            cursor = conn.cursor()
            
            cursor.execute("SELECT raw_result FROM analysis_results WHERE id = %s", (analysis_id,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return json.loads(row[0])
            return None
            
        except Exception as e:
            print(f"Error getting analysis from PostgreSQL: {str(e)}")
            return None
    
    def _get_by_id_sqlite(self, analysis_id: int) -> Optional[Dict[str, Any]]:
        """Get analysis by ID from SQLite"""
        try:
            conn = sqlite3.connect('historical_analysis.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT raw_result FROM analysis_results WHERE id = ?", (analysis_id,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return json.loads(row[0])
            return None
            
        except Exception as e:
            print(f"Error getting analysis from SQLite: {str(e)}")
            return None
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            if self.db_type == 'supabase':
                return self.supabase.get_database_stats()
            elif self.db_type == 'postgresql':
                return self._get_stats_postgresql()
            else:
                return self._get_stats_sqlite()
        except Exception as e:
            print(f"Error getting database stats: {str(e)}")
            return {}
    
    def _get_stats_postgresql(self) -> Dict[str, Any]:
        """Get PostgreSQL database statistics"""
        if psycopg2 is None:
            return self._get_stats_sqlite()
            
        try:
            conn = psycopg2.connect(os.getenv('DATABASE_URL'))
            cursor = conn.cursor()
            
            # Total records
            cursor.execute("SELECT COUNT(*) FROM analysis_results")
            total_records = cursor.fetchone()[0]
            
            # Records by year
            cursor.execute("""
                SELECT year, COUNT(*) 
                FROM analysis_results 
                WHERE year IS NOT NULL 
                GROUP BY year 
                ORDER BY year DESC 
                LIMIT 10
            """)
            by_year = cursor.fetchall()
            
            # AI generated count
            cursor.execute("""
                SELECT COUNT(*) 
                FROM analysis_results 
                WHERE ai_generated_probability > 70
            """)
            ai_generated_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'database_type': 'PostgreSQL',
                'total_records': total_records,
                'records_by_year': dict(by_year),
                'likely_ai_generated': ai_generated_count
            }
            
        except Exception as e:
            print(f"Error getting PostgreSQL stats: {str(e)}")
            return {}
    
    def _get_stats_sqlite(self) -> Dict[str, Any]:
        """Get SQLite database statistics"""
        try:
            conn = sqlite3.connect('historical_analysis.db')
            cursor = conn.cursor()
            
            # Total records
            cursor.execute("SELECT COUNT(*) FROM analysis_results")
            total_records = cursor.fetchone()[0]
            
            # Records by year
            cursor.execute("""
                SELECT year, COUNT(*) 
                FROM analysis_results 
                WHERE year IS NOT NULL 
                GROUP BY year 
                ORDER BY year DESC 
                LIMIT 10
            """)
            by_year = cursor.fetchall()
            
            # AI generated count
            cursor.execute("""
                SELECT COUNT(*) 
                FROM analysis_results 
                WHERE ai_generated_probability > 70
            """)
            ai_generated_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'database_type': 'SQLite',
                'total_records': total_records,
                'records_by_year': dict(by_year) if by_year else {},
                'likely_ai_generated': ai_generated_count
            }
            
        except Exception as e:
            print(f"Error getting SQLite stats: {str(e)}")
            return {}