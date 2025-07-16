# Historical Image Analysis AI Pipeline

## Overview

This is an enhanced Streamlit-based AI application that analyzes historical images to identify and describe historical events. The system now supports multiple image uploads, WebP format, and provides advanced features including exact date detection, AI generation probability assessment, and Wikipedia URL integration.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes (July 2025)

- Enhanced to support multiple image uploads simultaneously
- Added WebP format support alongside JPG, PNG, JPEG
- Integrated exact date detection with confidence scoring
- Added AI-generated image detection capability
- Implemented Wikipedia URL generation for identified events
- Simplified architecture to use OpenAI GPT-4o Vision as primary analysis engine
- Added batch processing and JSON export for multiple images
- **Added comprehensive database functionality:**
  - Supabase database integration (primary)
  - PostgreSQL database integration with SQLite fallback
  - Automatic storage of all analysis results with image URLs
  - Analysis history browsing with 50 most recent results
  - Search functionality across events, titles, and locations
  - Database statistics with visual charts by historical year
  - Full result retrieval by database ID
  - Image file storage with URL generation
- **Enhanced celebrity detection with comma-separated names storage**
- **Added comprehensive results table displaying all metadata**
- **Implemented step-by-step processing logs for debugging**
- **Added image optimization with WebP conversion and size limits**
- **Fixed Vercel deployment configuration (Note: Streamlit requires persistent server environment)**

## System Architecture

The application follows a modular pipeline architecture where each component handles a specific aspect of image analysis:

1. **Frontend**: Streamlit web interface for user interaction
2. **Image Processing Pipeline**: Sequential processing through multiple AI models
3. **AI Model Integration**: Combination of computer vision and language models
4. **External API Integration**: OpenAI GPT-4o for historical inference

## Key Components

### Core Processing Modules

- **ImageProcessor**: Handles image preprocessing (resizing, contrast enhancement, color normalization)
- **OCRExtractor**: Extracts text from images using Tesseract OCR
- **VisualCaptioner**: Generates scene descriptions using BLIP (Salesforce/blip-image-captioning-base)
- **ObjectDetector**: Detects objects using YOLOv8 nano model
- **HistoricalInference**: Analyzes all extracted data using OpenAI GPT-4o to identify historical events

### Supporting Components

- **DatabaseManager**: Handles Supabase/PostgreSQL/SQLite database operations for storing and retrieving analysis results
- **SupabaseManager**: Direct Supabase REST API integration for cloud database storage
- **Utils**: Geographic utilities for location name to GPS coordinate conversion using geopy
- **App.py**: Main Streamlit application orchestrating the pipeline with multi-page navigation

## Data Flow

1. **Image Upload**: User uploads images through Streamlit interface (supports multiple files and WebP format)
2. **Preprocessing**: Images are resized to 1024px width and optimized
3. **AI Analysis**: Direct analysis using OpenAI GPT-4o Vision model for comprehensive historical inference
4. **Data Enhancement**:
   - GPS coordinate conversion for identified locations
   - Wikipedia URL generation for events
   - Confidence scoring for all identified elements
5. **Database Storage**: All results automatically saved to Supabase cloud database (with PostgreSQL/SQLite fallback)
6. **Result Display**: Structured historical event information with database management features

The pipeline returns:
- Event title and description with confidence scores
- Exact dates (when determinable) and historical year
- Location name and GPS coordinates
- AI-generation probability assessment
- Wikipedia search and direct article links
- Image URL for uploaded files
- Database record ID for future reference

## Navigation Pages

1. **Analyze Images**: Main analysis interface with batch processing
2. **Analysis History**: Browse 50 most recent analysis results
3. **Search Results**: Search database by event, title, or location
4. **Database Statistics**: Visual charts and statistics overview

## External Dependencies

### AI Models
- **OpenAI GPT-4o**: Primary model for historical inference (requires OPENAI_API_KEY)
- **BLIP Image Captioning**: Salesforce/blip-image-captioning-base from Hugging Face
- **YOLOv8**: Ultralytics YOLOv8 nano model for object detection
- **Tesseract OCR**: Text extraction from images

### Python Libraries
- **Streamlit**: Web application framework
- **OpenCV**: Image processing operations
- **PIL/Pillow**: Image manipulation
- **PyTorch**: Deep learning framework for BLIP model
- **Transformers**: Hugging Face model loading
- **pytesseract**: OCR functionality
- **geopy**: Geographic coordinate conversion

## Deployment Strategy

The application is designed for cloud deployment with the following considerations:

### Resource Requirements
- GPU support recommended for faster inference (PyTorch models)
- Sufficient memory for loading multiple AI models
- Internet connectivity for OpenAI API calls and geocoding

### Environment Variables
- `OPENAI_API_KEY`: Required for historical inference functionality
- Tesseract OCR installation required on system

### Model Caching
- Uses Streamlit's `@st.cache_resource` decorator to prevent reloading models on each request
- Models are loaded once and reused across sessions

### Fallback Mechanisms
- OCR extraction includes error handling for processing failures
- Object detection has fallback responses when models fail to load
- Historical inference includes fallback responses when OpenAI API is unavailable

The architecture prioritizes modularity and fault tolerance, allowing individual components to fail gracefully without breaking the entire pipeline. Each processing step is independent and can be enhanced or replaced without affecting other components.