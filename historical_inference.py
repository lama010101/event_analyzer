import os
import json
from openai import OpenAI

class HistoricalInference:
    """Uses OpenAI GPT-4o to infer historical events from image analysis data"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            print("Warning: OPENAI_API_KEY not found in environment variables")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key)
    
    def infer_historical_event(self, caption, image_text, detected_objects):
        """
        Analyze image metadata to determine the historical event
        Returns structured information about the identified event
        """
        if self.client is None:
            return self._get_fallback_response()
        
        try:
            # Prepare the prompt with all available data
            prompt = self._create_analysis_prompt(caption, image_text, detected_objects)
            
            # Call OpenAI API
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=1000
            )
            
            # Parse the response
            result = json.loads(response.choices[0].message.content)
            
            # Validate and clean the result
            validated_result = self._validate_result(result)
            
            return validated_result
        
        except Exception as e:
            print(f"Error during historical inference: {str(e)}")
            return self._get_error_response(str(e))
    
    def _get_system_prompt(self):
        """Get the system prompt for historical analysis"""
        return """You are a world-class historian and image analyst specializing in identifying historical events from visual evidence. 

Your task is to analyze image metadata (visual description, detected text, and identified objects) to determine the exact historical event shown in the image.

You must provide detailed, accurate historical information with confidence scores for your analysis.

Always respond with valid JSON containing all required fields. Be specific about events - avoid generic descriptions like "a historical photo" or "people gathering". Identify the actual historical event if possible.

If you cannot identify a specific event, provide the most likely historical context based on visual clues (time period, location, type of event)."""
    
    def _create_analysis_prompt(self, caption, image_text, detected_objects):
        """Create the analysis prompt with all available data"""
        objects_str = ", ".join(detected_objects) if detected_objects else "None detected"
        text_str = image_text if image_text else "No text detected"
        
        prompt = f"""Given this image metadata, determine the exact historical event shown:

VISUAL DESCRIPTION: {caption}

DETECTED TEXT: {text_str}

DETECTED OBJECTS: {objects_str}

Analyze this information to identify the specific historical event. Consider:
- Time period indicators (clothing, vehicles, architecture, technology)
- Location clues (landmarks, signs, geographic features)
- Event type (political, military, social, cultural)
- Historical context and significance

Provide your analysis in JSON format with these exact fields:
- "title": Brief, specific title of the event
- "event": Name of the historical event
- "description": 3-4 sentence detailed description of what's happening
- "location_name": Precise location (e.g., "Brandenburg Gate, Berlin, Germany")
- "year": Year when this occurred (numeric)
- "confidence": Object with "year", "location", and "event" scores (0-100)

Be as specific as possible. If you can't identify the exact event, provide the most likely historical context based on the evidence."""
        
        return prompt
    
    def _validate_result(self, result):
        """Validate and clean the API response"""
        # Ensure all required fields are present
        required_fields = ['title', 'event', 'description', 'location_name', 'year', 'confidence']
        
        for field in required_fields:
            if field not in result:
                result[field] = self._get_default_value(field)
        
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
    
    def _get_default_value(self, field):
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
    
    def _get_fallback_response(self):
        """Return fallback response when API is not available"""
        return {
            'title': 'API Not Available',
            'event': 'Historical Analysis Unavailable',
            'description': 'OpenAI API key not configured. Cannot perform historical inference.',
            'location_name': 'Unknown',
            'year': 'Unknown',
            'confidence': {'year': 0, 'location': 0, 'event': 0}
        }
    
    def _get_error_response(self, error_message):
        """Return error response"""
        return {
            'title': 'Analysis Error',
            'event': 'Error During Analysis',
            'description': f'Error occurred during historical analysis: {error_message}',
            'location_name': 'Unknown',
            'year': 'Unknown',
            'confidence': {'year': 0, 'location': 0, 'event': 0}
        }
