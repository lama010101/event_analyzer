import streamlit as st
import json
from PIL import Image
import io
import base64
import os
from openai import OpenAI

# Initialize OpenAI client
@st.cache_resource
def get_openai_client():
    """Initialize OpenAI client"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)

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

Provide your analysis in JSON format with these exact fields:
- "title": Brief, specific title of the event
- "event": Name of the historical event
- "description": 3-4 sentence detailed description of what's happening
- "location_name": Precise location (e.g., "Brandenburg Gate, Berlin, Germany")
- "year": Year when this occurred (numeric)
- "confidence": Object with "year", "location", and "event" scores (0-100)
- "extracted_text": Any visible text you can see in the image
- "visual_elements": Key visual elements that helped with identification

Be as specific as possible. If you can't identify the exact event, provide the most likely historical context based on the evidence."""
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
    required_fields = ['title', 'event', 'description', 'location_name', 'year', 'confidence']
    
    for field in required_fields:
        if field not in result:
            result[field] = get_default_value(field)
    
    # Validate confidence scores
    if 'confidence' in result and isinstance(result['confidence'], dict):
        confidence = result['confidence']
        for score_type in ['year', 'location', 'event']:
            if score_type not in confidence:
                confidence[score_type] = 50
            else:
                # Ensure confidence is between 0-100
                confidence[score_type] = max(0, min(100, int(confidence[score_type])))
    else:
        result['confidence'] = {'year': 50, 'location': 50, 'event': 50}
    
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
    
    return result

def get_default_value(field):
    """Get default value for missing fields"""
    defaults = {
        'title': 'Historical Event',
        'event': 'Unidentified Historical Event',
        'description': 'Unable to determine specific historical event from available evidence.',
        'location_name': 'Unknown Location',
        'year': 'Unknown',
        'confidence': {'year': 0, 'location': 0, 'event': 0}
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
        'confidence': {'year': 0, 'location': 0, 'event': 0}
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

def main():
    st.set_page_config(
        page_title="Historical Image Analysis Pipeline",
        page_icon="🏛️",
        layout="wide"
    )
    
    st.title("🏛️ Historical Image Analysis Pipeline")
    st.markdown("Upload a historical image to extract detailed event information including title, description, date, location, and GPS coordinates.")
    
    # Initialize OpenAI client
    client = get_openai_client()
    
    if client is None:
        st.error("❌ OpenAI API key not found. Please add your OPENAI_API_KEY to continue.")
        st.info("Go to https://platform.openai.com/api-keys to get your API key.")
        st.stop()
    else:
        st.success("✅ OpenAI client initialized successfully!")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a historical image...",
        type=['jpg', 'jpeg', 'png'],
        help="Upload JPG, JPEG, or PNG images"
    )
    
    if uploaded_file is not None:
        # Display uploaded image
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📷 Uploaded Image")
            image = Image.open(uploaded_file)
            st.image(image, caption="Original Image", use_column_width=True)
        
        with col2:
            st.subheader("🔄 Processing Status")
            
            # Process button
            if st.button("🚀 Analyze Historical Image", type="primary"):
                try:
                    with st.spinner("Analyzing image with AI..."):
                        st.write("🧠 Processing image through GPT-4o Vision...")
                        historical_result = analyze_historical_image(client, image)
                        
                        # Get GPS coordinates if location is identified
                        if historical_result.get('location_name') and historical_result['location_name'] != 'Unknown Location':
                            st.write("🌍 Looking up GPS coordinates...")
                            gps_coords = get_gps_coordinates(historical_result['location_name'])
                            historical_result['gps'] = gps_coords
                    
                    st.success("✅ Analysis complete!")
                    
                    # Display results
                    st.subheader("📊 Analysis Results")
                    
                    # Main event card
                    st.markdown("### 🏛️ Historical Event Identified")
                    
                    col_a, col_b = st.columns([2, 1])
                    
                    with col_a:
                        st.markdown(f"**Title:** {historical_result.get('title', 'Unknown')}")
                        st.markdown(f"**Event:** {historical_result.get('event', 'Unknown')}")
                        st.markdown(f"**Description:** {historical_result.get('description', 'No description available')}")
                        st.markdown(f"**Year:** {historical_result.get('year', 'Unknown')}")
                        st.markdown(f"**Location:** {historical_result.get('location_name', 'Unknown')}")
                        
                        if historical_result.get('gps'):
                            gps = historical_result['gps']
                            st.markdown(f"**GPS Coordinates:** {gps[0]:.4f}, {gps[1]:.4f}")
                    
                    with col_b:
                        if historical_result.get('confidence'):
                            st.markdown("**Confidence Scores:**")
                            confidence = historical_result['confidence']
                            st.metric("Year", f"{confidence.get('year', 0)}%")
                            st.metric("Location", f"{confidence.get('location', 0)}%")
                            st.metric("Event", f"{confidence.get('event', 0)}%")
                    
                    # Detailed analysis in expandable sections
                    with st.expander("📝 Extracted Text"):
                        if historical_result.get('extracted_text'):
                            st.text(historical_result['extracted_text'])
                        else:
                            st.write("No text detected in the image.")
                    
                    with st.expander("👁️ Visual Elements"):
                        if historical_result.get('visual_elements'):
                            if isinstance(historical_result['visual_elements'], list):
                                for element in historical_result['visual_elements']:
                                    st.write(f"- {element}")
                            else:
                                st.write(historical_result['visual_elements'])
                        else:
                            st.write("No specific visual elements identified.")
                    
                    with st.expander("📄 Raw JSON Output"):
                        final_output = {
                            "title": historical_result.get('title'),
                            "description": historical_result.get('description'),
                            "location_name": historical_result.get('location_name'),
                            "gps": historical_result.get('gps'),
                            "year": historical_result.get('year'),
                            "event": historical_result.get('event'),
                            "confidence": historical_result.get('confidence', {})
                        }
                        st.json(final_output)
                        
                        # Download button for JSON
                        json_str = json.dumps(final_output, indent=2)
                        st.download_button(
                            label="📥 Download JSON Result",
                            data=json_str,
                            file_name="historical_analysis.json",
                            mime="application/json"
                        )
                
                except Exception as e:
                    st.error(f"❌ Error during analysis: {str(e)}")
                    st.exception(e)
    
    # Information section
    st.markdown("---")
    st.markdown("### ℹ️ How it works")
    st.markdown("""
    This AI system performs the following analysis:
    1. **Image Analysis**: Uses OpenAI's GPT-4o Vision to analyze the complete image
    2. **Historical Identification**: Identifies specific historical events based on visual clues
    3. **Text Extraction**: Detects any visible text or signs in the image
    4. **Visual Element Analysis**: Identifies key objects, people, and contextual elements
    5. **Location & Date Inference**: Determines when and where the event occurred
    6. **Confidence Assessment**: Provides accuracy scores for different aspects of the analysis
    7. **GPS Lookup**: Converts location names to coordinates when possible
    """)

if __name__ == "__main__":
    main()
