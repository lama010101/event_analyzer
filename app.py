import streamlit as st
import json
from PIL import Image
import io
import base64
import os
import requests
import urllib.parse
from openai import OpenAI
from database import DatabaseManager
from firebase_storage import FirebaseStorageManager

# Initialize OpenAI client
@st.cache_resource
def get_openai_client():
    """Initialize OpenAI client"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)

# Initialize database
@st.cache_resource
def get_database():
    """Initialize database connection"""
    return DatabaseManager()

# Initialize Firebase Storage
@st.cache_resource
def get_firebase_storage():
    """Initialize Firebase Storage"""
    return FirebaseStorageManager()

def image_to_base64(image):
    """Convert PIL Image to base64 string"""
    buffer = io.BytesIO()
    image.save(buffer, format='JPEG')
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    return image_base64

def analyze_historical_image(client, image):
    """Analyze historical image using OpenAI GPT-4o vision"""
    try:
        # Convert image to base64
        image_base64 = image_to_base64(image)
        
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": """You are a world-class historian and image analyst specializing in identifying historical events from photographs. 

Your task is to analyze the image and determine the exact historical event shown. Provide detailed, accurate historical information.

Always respond with valid JSON containing all required fields. Be specific about events - avoid generic descriptions like "a historical photo" or "people gathering". Identify the actual historical event if possible."""
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Analyze this historical image and identify the specific event. Consider:
- Time period indicators (clothing, vehicles, architecture, technology)
- Location clues (landmarks, signs, geographic features)
- Event type (political, military, social, cultural)
- Historical context and significance
- Any visible text or signs
- Signs that this might be an AI-generated image vs authentic historical photo

Provide your analysis in JSON format with these exact fields:
- "title": Brief, specific title of the event
- "event": Name of the historical event
- "description": 3-4 sentence detailed description of what's happening
- "location_name": Precise location (e.g., "Brandenburg Gate, Berlin, Germany")
- "year": Year when this occurred (numeric)
- "exact_date": Specific date if determinable (YYYY-MM-DD format, or "Unknown")
- "confidence": Object with "year", "location", "event", and "exact_date" scores (0-100)
- "ai_generated_probability": Percentage likelihood this is AI-generated (0-100)
- "ai_analysis": Explanation of AI generation assessment
- "extracted_text": Any visible text you can see in the image
- "visual_elements": Key visual elements that helped with identification
- "prompt": Detailed description that could be used by an AI image generator to recreate this image, including style, composition, lighting, historical period, clothing, architecture, and atmosphere
- "celebrity": Boolean true if image contains a famous person with a Wikipedia page, false otherwise
- "celebrity_name": If celebrity is true, provide the name(s) of the famous person(s), separated by commas if multiple

Be as specific as possible about dates. If you can identify the exact date, provide it. Carefully analyze for signs of AI generation such as inconsistent details, impossible combinations, or artifacts."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=1500
        )
        
        result = json.loads(response.choices[0].message.content)
        return validate_result(result)
        
    except Exception as e:
        st.error(f"Error analyzing image: {str(e)}")
        return get_error_response(str(e))

def validate_result(result):
    """Validate and clean the API response"""
    # Ensure all required fields are present
    required_fields = ['title', 'event', 'description', 'location_name', 'year', 'exact_date', 'confidence', 'ai_generated_probability', 'prompt', 'celebrity', 'celebrity_name']
    
    for field in required_fields:
        if field not in result:
            result[field] = get_default_value(field)
    
    # Validate confidence scores
    if 'confidence' in result and isinstance(result['confidence'], dict):
        confidence = result['confidence']
        for score_type in ['year', 'location', 'event', 'exact_date']:
            if score_type not in confidence:
                confidence[score_type] = 50
            else:
                # Ensure confidence is between 0-100
                confidence[score_type] = max(0, min(100, int(confidence[score_type])))
    else:
        result['confidence'] = {'year': 50, 'location': 50, 'event': 50, 'exact_date': 0}
    
    # Validate year
    if 'year' in result:
        try:
            year = int(result['year'])
            # Ensure reasonable year range
            if year < 1800 or year > 2024:
                result['year'] = "Unknown"
            else:
                result['year'] = year
        except:
            result['year'] = "Unknown"
    
    # Validate AI generation probability
    if 'ai_generated_probability' in result:
        try:
            ai_prob = int(result['ai_generated_probability'])
            result['ai_generated_probability'] = max(0, min(100, ai_prob))
        except:
            result['ai_generated_probability'] = 0
    
    return result

def get_default_value(field):
    """Get default value for missing fields"""
    defaults = {
        'title': 'Historical Event',
        'event': 'Unidentified Historical Event',
        'description': 'Unable to determine specific historical event from available evidence.',
        'location_name': 'Unknown Location',
        'year': 'Unknown',
        'exact_date': 'Unknown',
        'confidence': {'year': 0, 'location': 0, 'event': 0, 'exact_date': 0},
        'ai_generated_probability': 0,
        'ai_analysis': 'Unable to determine if AI-generated',
        'prompt': 'Historical photograph with unidentified subjects and context',
        'celebrity': False,
        'celebrity_name': None
    }
    return defaults.get(field, 'Unknown')

def get_error_response(error_message):
    """Return error response"""
    return {
        'title': 'Analysis Error',
        'event': 'Error During Analysis',
        'description': f'Error occurred during historical analysis: {error_message}',
        'location_name': 'Unknown',
        'year': 'Unknown',
        'exact_date': 'Unknown',
        'confidence': {'year': 0, 'location': 0, 'event': 0, 'exact_date': 0},
        'ai_generated_probability': 0,
        'ai_analysis': 'Could not analyze due to error',
        'prompt': 'Error occurred during analysis',
        'celebrity': False,
        'celebrity_name': None
    }

def get_gps_coordinates(location_name):
    """Simple geocoding function (simplified version)"""
    # This is a simplified version - in production, you'd use a proper geocoding service
    common_locations = {
        'berlin, germany': [52.5200, 13.4050],
        'new york, usa': [40.7128, -74.0060],
        'london, england': [51.5074, -0.1278],
        'paris, france': [48.8566, 2.3522],
        'washington dc, usa': [38.9072, -77.0369],
        'moscow, russia': [55.7558, 37.6176],
        'beijing, china': [39.9042, 116.4074],
        'tokyo, japan': [35.6762, 139.6503]
    }
    
    location_lower = location_name.lower()
    for key, coords in common_locations.items():
        if key in location_lower:
            return coords
    
    return None

def generate_wikipedia_url(event_name, location=None):
    """Generate Wikipedia search URL for the historical event"""
    try:
        # Create search terms
        search_terms = [event_name]
        if location:
            search_terms.append(f"{event_name} {location}")
        
        # Try the most specific search term first
        search_term = search_terms[-1] if len(search_terms) > 1 else search_terms[0]
        
        # Create Wikipedia search URL
        encoded_term = urllib.parse.quote(search_term)
        search_url = f"https://en.wikipedia.org/wiki/Special:Search?search={encoded_term}"
        
        # Also try direct article URL (replace spaces with underscores)
        article_title = search_term.replace(' ', '_')
        article_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(article_title)}"
        
        return {
            'title': f"Wikipedia: {search_term}",
            'search_url': search_url,
            'direct_url': article_url,
            'summary': f"Search Wikipedia for information about {search_term}"
        }
        
    except Exception as e:
        print(f"Error generating Wikipedia URL: {str(e)}")
        return None

def save_image_and_get_url(uploaded_file, image_index, firebase_manager, log_container=None):
    """Upload optimized image to Firebase Storage and return URL"""
    def log_message(message):
        print(message)
        if log_container:
            log_container.write(f"🔄 {message}")
    
    try:
        log_message(f"Processing image {image_index}: {uploaded_file.name}")
        
        # Try Firebase upload first
        firebase_url = firebase_manager.upload_image(uploaded_file, image_index, log_container)
        
        if firebase_url:
            log_message("✅ Image uploaded to Firebase Storage successfully")
            return firebase_url
        
        # Fallback to local storage if Firebase fails
        log_message("⚠️ Firebase requires service account credentials - using optimized local storage")
        import os, io
        uploads_dir = "uploaded_images"
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)
        
        # Generate unique filename and optimize the image
        from datetime import datetime
        from PIL import Image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = uploaded_file.name.split('.')[0].replace(' ', '_').replace('(', '').replace(')', '')
        
        log_message("🔄 Optimizing image for local storage...")
        
        # Load and optimize image
        image = Image.open(io.BytesIO(uploaded_file.getvalue()))
        log_message(f"Original size: {image.width}x{image.height}")
        
        # Create optimized WebP version
        firebase_manager.optimize_image(image)  # This will optimize it
        
        # Convert to WebP format
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if 'A' in image.mode else None)
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
            
        # Resize if too large (desktop optimization)
        if image.width > 1200:
            ratio = 1200 / image.width
            new_height = int(image.height * ratio)
            image = image.resize((1200, new_height), Image.Resampling.LANCZOS)
            log_message(f"Resized to: {image.width}x{image.height}")
        
        # Save as optimized WebP
        filename = f"{timestamp}_{image_index}_{base_filename}.webp"
        filepath = os.path.join(uploads_dir, filename)
        
        image.save(filepath, format='WebP', quality=85, optimize=True)
        log_message(f"📁 Saved optimized WebP: {filepath}")
        
        return f"local_storage://{filepath}"
        
    except Exception as e:
        error_msg = f"Error saving image: {str(e)}"
        log_message(f"❌ {error_msg}")
        return None

def process_multiple_images(client, images, uploaded_files, db, firebase_manager):
    """Process multiple images and return results"""
    results = []
    
    # Create log container
    log_container = st.expander("📋 Processing Log", expanded=True)
    
    for i, image in enumerate(images):
        st.write(f"🔍 Analyzing image {i+1} of {len(images)}...")
        log_container.write(f"\n--- Processing Image {i+1}: {uploaded_files[i].name if i < len(uploaded_files) else f'image_{i+1}'} ---")
        
        try:
            # Save image and get URL
            image_url = None
            if i < len(uploaded_files):
                image_url = save_image_and_get_url(uploaded_files[i], i+1, firebase_manager, log_container)
                if image_url:
                    if image_url.startswith('https://'):
                        st.write(f"📤 Image uploaded to Firebase Storage: {image_url}")
                    else:
                        st.write(f"📁 Image optimized and stored locally (WebP format, 1200px max width)")
            
            # Analyze the image
            log_container.write("🤖 Starting AI analysis...")
            result = analyze_historical_image(client, image)
            log_container.write("✅ AI analysis complete")
            
            # Get GPS coordinates if location is identified
            if result.get('location_name') and result['location_name'] != 'Unknown Location':
                log_container.write(f"🗺️ Looking up GPS coordinates for: {result['location_name']}")
                gps_coords = get_gps_coordinates(result['location_name'])
                result['gps'] = gps_coords
                if gps_coords:
                    log_container.write(f"📍 GPS found: {gps_coords}")
            
            # Generate Wikipedia URL
            if result.get('event') and result['event'] != 'Unidentified Historical Event':
                log_container.write(f"🔗 Generating Wikipedia URLs for: {result['event']}")
                wiki_info = generate_wikipedia_url(result['event'], result.get('location_name'))
                result['wikipedia'] = wiki_info
            
            result['image_index'] = i + 1
            result['image_url'] = image_url
            
            # Save to database
            image_name = uploaded_files[i].name if i < len(uploaded_files) else f"image_{i+1}"
            log_container.write(f"💾 Saving to Supabase database...")
            db_id = db.save_analysis_result(result, image_name, image_url)
            if db_id:
                result['database_id'] = db_id
                st.write(f"✅ Saved to database (ID: {db_id})")
                log_container.write(f"✅ Database record created with ID: {db_id}")
            else:
                st.write("⚠️ Database save failed - check logs")
                log_container.write("❌ Database save failed")
            
            results.append(result)
            
        except Exception as e:
            error_result = get_error_response(str(e))
            error_result['image_index'] = i + 1
            results.append(error_result)
            log_container.write(f"❌ Error processing image {i+1}: {str(e)}")
    
    return results

def main():
    st.set_page_config(
        page_title="Historical Image Analysis Pipeline",
        page_icon="🏛️",
        layout="wide"
    )
    
    st.title("🏛️ Historical Image Analysis Pipeline")
    st.markdown("Upload historical images to extract detailed event information including title, description, date, location, and GPS coordinates. All results are saved to the database for future reference.")
    
    # Initialize OpenAI client, database, and Firebase storage
    client = get_openai_client()
    db = get_database()
    firebase_manager = get_firebase_storage()
    
    if client is None:
        st.error("❌ OpenAI API key not found. Please add your OPENAI_API_KEY to continue.")
        st.info("Go to https://platform.openai.com/api-keys to get your API key.")
        st.stop()
    else:
        st.success("✅ OpenAI client and database initialized successfully!")
    
    # Sidebar for navigation
    st.sidebar.title("📊 Navigation")
    page = st.sidebar.selectbox("Choose a page:", [
        "🔍 Analyze Images", 
        "📚 Analysis History", 
        "🔎 Search Results", 
        "📈 Database Statistics"
    ])
    
    if page == "🔍 Analyze Images":
        analyze_images_page(client, db, firebase_manager)
    elif page == "📚 Analysis History":
        history_page(db)
    elif page == "🔎 Search Results":
        search_page(db)
    elif page == "📈 Database Statistics":
        statistics_page(db)

def analyze_images_page(client, db, firebase_manager):
    """Main image analysis page"""
    
    # File upload - Multiple files
    uploaded_files = st.file_uploader(
        "Choose historical images...",
        type=['jpg', 'jpeg', 'png', 'webp'],
        help="Upload JPG, JPEG, PNG, or WebP images",
        accept_multiple_files=True
    )
    
    if uploaded_files:
        st.subheader(f"📷 Uploaded Images ({len(uploaded_files)} files)")
        
        # Display uploaded images in a grid
        cols = st.columns(min(3, len(uploaded_files)))
        images = []
        
        for i, uploaded_file in enumerate(uploaded_files):
            try:
                image = Image.open(uploaded_file)
                # Convert WebP to RGB if needed
                if image.format == 'WEBP' or image.mode != 'RGB':
                    image = image.convert('RGB')
                images.append(image)
                
                with cols[i % 3]:
                    st.image(image, caption=f"Image {i+1}: {uploaded_file.name}", use_container_width=True)
            except Exception as e:
                st.error(f"Error loading {uploaded_file.name}: {str(e)}")
        
        st.subheader("🔄 Processing Controls")
        
        # Process button
        if st.button("🚀 Analyze All Historical Images", type="primary"):
            try:
                with st.spinner("Analyzing images with AI..."):
                    # Process all images
                    all_results = process_multiple_images(client, images, uploaded_files, db, firebase_manager)
                
                st.success(f"✅ Analysis complete for {len(all_results)} images!")
                
                # Display results in a comprehensive table
                st.subheader("📊 Complete Analysis Results")
                
                # Prepare data for the table
                table_data = []
                for result in all_results:
                    row = {
                        "Image": f"Image {result['image_index']}",
                        "Title": result.get('title', 'Unknown'),
                        "Event": result.get('event', 'Unknown'),
                        "Year": result.get('year', 'Unknown'),
                        "Date": result.get('exact_date', 'Unknown'),
                        "Location": result.get('location_name', 'Unknown'),
                        "Celebrity": "✅ Yes" if result.get('celebrity') else "❌ No",
                        "Celebrity Names": result.get('celebrity_name', 'None'),
                        "AI Generated": f"{result.get('ai_generated_probability', 0)}%",
                        "Database ID": result.get('database_id', 'N/A'),
                        "Image URL": result.get('image_url', 'N/A')
                    }
                    table_data.append(row)
                
                # Display the table
                import pandas as pd
                df = pd.DataFrame(table_data)
                st.dataframe(df, use_container_width=True)
                
                # Display detailed results for each image
                st.subheader("📋 Detailed Analysis Results")
                for result in all_results:
                    with st.expander(f"Image {result['image_index']}: {result.get('title', 'Unknown')}", expanded=False):
                        
                        # Create columns for main results
                        col_a, col_b = st.columns([2, 1])
                        
                        with col_a:
                            st.markdown(f"**Event:** {result.get('event', 'Unknown')}")
                            st.markdown(f"**Description:** {result.get('description', 'No description available')}")
                            st.markdown(f"**Year:** {result.get('year', 'Unknown')}")
                            if result.get('exact_date') and result['exact_date'] != 'Unknown':
                                st.markdown(f"**Exact Date:** {result['exact_date']}")
                            st.markdown(f"**Location:** {result.get('location_name', 'Unknown')}")
                            
                            if result.get('gps'):
                                gps = result['gps']
                                st.markdown(f"**GPS Coordinates:** {gps[0]:.4f}, {gps[1]:.4f}")
                            
                            # Celebrity information
                            if result.get('celebrity'):
                                st.markdown(f"**Celebrity Detected:** ✅ Yes")
                                if result.get('celebrity_name'):
                                    st.markdown(f"**Celebrity Names:** {result['celebrity_name']}")
                            else:
                                st.markdown(f"**Celebrity Detected:** ❌ No")
                            
                            # AI Generation Prompt
                            if result.get('prompt'):
                                st.markdown("**AI Recreation Prompt:**")
                                st.text_area("AI Image Generation Prompt", value=result['prompt'], height=100, key=f"prompt_{result['image_index']}", label_visibility="collapsed")
                            
                            if result.get('database_id'):
                                st.markdown(f"**Database ID:** {result['database_id']}")
                            
                            if result.get('image_url'):
                                st.markdown(f"**Image URL:** {result['image_url']}")
                                
                            # Wikipedia links
                            if result.get('wikipedia'):
                                wiki = result['wikipedia']
                                st.markdown("**Wikipedia Links:**")
                                st.markdown(f"[Search Wikipedia]({wiki.get('search_url', '#')})")
                                st.markdown(f"[Direct Article]({wiki.get('direct_url', '#')})")
                        
                        with col_b:
                            # AI Generation Assessment
                            ai_prob = result.get('ai_generated_probability', 0)
                            if ai_prob > 70:
                                st.error(f"🤖 Likely AI-Generated: {ai_prob}%")
                            elif ai_prob > 30:
                                st.warning(f"🤔 Possibly AI-Generated: {ai_prob}%")
                            else:
                                st.success(f"📸 Likely Authentic: {100-ai_prob}% confidence")
                            
                            # Confidence scores
                            if result.get('confidence'):
                                st.markdown("**Confidence Scores:**")
                                confidence = result['confidence']
                                st.metric("Year", f"{confidence.get('year', 0)}%")
                                st.metric("Location", f"{confidence.get('location', 0)}%")
                                st.metric("Event", f"{confidence.get('event', 0)}%")
                                if confidence.get('exact_date', 0) > 0:
                                    st.metric("Exact Date", f"{confidence.get('exact_date', 0)}%")
                                    
                            # Text extraction
                            if result.get('extracted_text') and result['extracted_text'] != 'No visible text detected':
                                st.markdown("**Extracted Text:**")
                                st.code(result['extracted_text'])
                                
                            # Visual elements
                            if result.get('visual_elements'):
                                st.markdown("**Visual Elements:**")
                                elements = result['visual_elements']
                                if isinstance(elements, list):
                                    for element in elements:
                                        st.markdown(f"• {element}")
                                else:
                                    st.markdown(elements)
                    
                    # Wikipedia integration
                    if result.get('wikipedia'):
                        with st.expander("📖 Wikipedia Resources"):
                            wiki = result['wikipedia']
                            st.markdown(f"**Search Results:** [Wikipedia Search]({wiki['search_url']})")
                            st.markdown(f"**Direct Article:** [Wikipedia Article]({wiki['direct_url']})")
                            st.write(wiki['summary'])
                    
                    # Detailed analysis in expandable sections
                    with st.expander("📝 Extracted Text"):
                        if result.get('extracted_text'):
                            st.text(result['extracted_text'])
                        else:
                            st.write("No text detected in the image.")
                    
                    with st.expander("👁️ Visual Elements"):
                        if result.get('visual_elements'):
                            if isinstance(result['visual_elements'], list):
                                for element in result['visual_elements']:
                                    st.write(f"- {element}")
                            else:
                                st.write(result['visual_elements'])
                        else:
                            st.write("No specific visual elements identified.")
                    
                    with st.expander("🤖 AI Generation Analysis"):
                        if result.get('ai_analysis'):
                            st.write(result['ai_analysis'])
                        else:
                            st.write("No AI generation analysis available.")
                    
                    with st.expander("📄 Raw JSON Output"):
                        final_output = {
                            "image_index": result.get('image_index'),
                            "title": result.get('title'),
                            "description": result.get('description'),
                            "location_name": result.get('location_name'),
                            "gps": result.get('gps'),
                            "year": result.get('year'),
                            "exact_date": result.get('exact_date'),
                            "event": result.get('event'),
                            "confidence": result.get('confidence', {}),
                            "ai_generated_probability": result.get('ai_generated_probability'),
                            "wikipedia": result.get('wikipedia')
                        }
                        st.json(final_output)
                    
                    st.markdown("---")  # Separator between results
                
                # Download all results as JSON
                all_results_json = json.dumps(all_results, indent=2)
                st.download_button(
                    label="📥 Download All Results (JSON)",
                    data=all_results_json,
                    file_name="historical_analysis_batch.json",
                    mime="application/json"
                )
                
            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                st.exception(e)

def history_page(db):
    """Display analysis history page"""
    st.header("📚 Analysis History")
    st.write("View your recent historical image analysis results.")
    
    # Get recent history
    history = db.get_analysis_history(50)
    
    if not history:
        st.info("No analysis history found. Analyze some images first!")
        return
    
    st.write(f"Showing {len(history)} recent analyses:")
    
    # Display history in a table-like format
    for item in history:
        with st.expander(f"{item['title']} - {item['event']} ({item['year']})"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Image:** {item['image_name']}")
                st.write(f"**Event:** {item['event']}")
                st.write(f"**Location:** {item['location_name']}")
                st.write(f"**Year:** {item['year']}")
                if item['exact_date'] and item['exact_date'] != 'Unknown':
                    st.write(f"**Exact Date:** {item['exact_date']}")
            
            with col2:
                st.write(f"**Analyzed:** {item['created_at']}")
                if item['ai_generated_probability'] is not None:
                    if item['ai_generated_probability'] > 70:
                        st.error(f"🤖 Likely AI-Generated: {item['ai_generated_probability']}%")
                    elif item['ai_generated_probability'] > 30:
                        st.warning(f"🤔 Possibly AI-Generated: {item['ai_generated_probability']}%")
                    else:
                        st.success(f"📸 Likely Authentic: {100-item['ai_generated_probability']}%")
                
                # View full details button
                if st.button(f"View Details", key=f"view_{item['id']}"):
                    full_result = db.get_analysis_by_id(item['id'])
                    if full_result:
                        st.json(full_result)

def search_page(db):
    """Search analysis results page"""
    st.header("🔎 Search Analysis Results")
    st.write("Search through your historical image analysis database.")
    
    # Search input
    search_query = st.text_input("Search by event, title, or location:", placeholder="e.g., Berlin Wall, World War, protests")
    
    if search_query:
        results = db.search_analysis_results(search_query, 20)
        
        if results:
            st.write(f"Found {len(results)} results for '{search_query}':")
            
            # Display search results
            for item in results:
                with st.expander(f"{item['title']} - {item['event']} ({item['year']})"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Image:** {item['image_name']}")
                        st.write(f"**Event:** {item['event']}")
                        st.write(f"**Location:** {item['location_name']}")
                        st.write(f"**Year:** {item['year']}")
                        if item['exact_date'] and item['exact_date'] != 'Unknown':
                            st.write(f"**Exact Date:** {item['exact_date']}")
                    
                    with col2:
                        st.write(f"**Analyzed:** {item['created_at']}")
                        if item['ai_generated_probability'] is not None:
                            if item['ai_generated_probability'] > 70:
                                st.error(f"🤖 Likely AI-Generated: {item['ai_generated_probability']}%")
                            elif item['ai_generated_probability'] > 30:
                                st.warning(f"🤔 Possibly AI-Generated: {item['ai_generated_probability']}%")
                            else:
                                st.success(f"📸 Likely Authentic: {100-item['ai_generated_probability']}%")
                        
                        # View full details button
                        if st.button(f"View Details", key=f"search_view_{item['id']}"):
                            full_result = db.get_analysis_by_id(item['id'])
                            if full_result:
                                st.json(full_result)
        else:
            st.info(f"No results found for '{search_query}'. Try different keywords.")
    else:
        st.info("Enter a search term to find analysis results.")

def statistics_page(db):
    """Display database statistics page"""
    st.header("📈 Database Statistics")
    st.write("Overview of your historical image analysis database.")
    
    # Get database statistics
    stats = db.get_database_stats()
    
    if stats:
        # Display main stats
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Analyses", stats.get('total_records', 0))
        
        with col2:
            st.metric("Database Type", stats.get('database_type', 'Unknown'))
        
        with col3:
            st.metric("Likely AI-Generated", stats.get('likely_ai_generated', 0))
        
        # Records by year chart
        if stats.get('records_by_year'):
            st.subheader("📊 Analyses by Historical Year")
            
            years = list(stats['records_by_year'].keys())
            counts = list(stats['records_by_year'].values())
            
            # Create a simple bar chart using Streamlit
            chart_data = {
                'Year': years,
                'Count': counts
            }
            st.bar_chart(chart_data)
            
            # Also show as table
            st.subheader("📋 Detailed Breakdown")
            for year, count in sorted(stats['records_by_year'].items(), key=lambda x: x[0], reverse=True):
                st.write(f"**{year}:** {count} analysis{'es' if count != 1 else ''}")
        
        # Database information
        st.subheader("🗄️ Database Information")
        st.write(f"**Type:** {stats.get('database_type')}")
        st.write(f"**Total Records:** {stats.get('total_records', 0)}")
        st.write(f"**AI-Generated Images Detected:** {stats.get('likely_ai_generated', 0)}")
        
    else:
        st.error("Unable to retrieve database statistics.")
    
    # Recent activity
    st.subheader("📅 Recent Activity")
    recent = db.get_analysis_history(5)
    
    if recent:
        for item in recent:
            st.write(f"• **{item['title']}** ({item['year']}) - analyzed on {item['created_at']}")
    else:
        st.info("No recent activity found.")
    
    # Information section
    st.markdown("---")
    st.markdown("### ℹ️ How it works")
    st.markdown("""
    This enhanced AI system performs the following analysis:
    1. **Multiple Image Support**: Upload and analyze several images at once (JPG, PNG, WebP)
    2. **Advanced Image Analysis**: Uses OpenAI's GPT-4o Vision for comprehensive analysis
    3. **Historical Event Identification**: Identifies specific events with exact dates when possible
    4. **AI Generation Detection**: Assesses likelihood that images are AI-generated vs authentic
    5. **Wikipedia Integration**: Automatically finds related Wikipedia articles for identified events
    6. **Text & Visual Analysis**: Extracts text and identifies key visual elements
    7. **Location & GPS Lookup**: Determines precise locations with GPS coordinates
    8. **Confidence Scoring**: Provides accuracy assessments for all analysis aspects
    9. **Batch Processing**: Download complete analysis results for all images as JSON
    """)

if __name__ == "__main__":
    main()
