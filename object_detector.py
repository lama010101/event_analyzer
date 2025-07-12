from ultralytics import YOLO
import cv2
import numpy as np
from PIL import Image

class ObjectDetector:
    """Detects objects in images using YOLOv8"""
    
    def __init__(self):
        try:
            # Load YOLOv8 model
            self.model = YOLO('yolov8n.pt')  # Using nano version for faster inference
            print("YOLOv8 model loaded successfully")
        except Exception as e:
            print(f"Error loading YOLOv8 model: {str(e)}")
            self.model = None
    
    def detect_objects(self, image):
        """
        Detect objects in the image and return relevant historical elements
        Returns a list of detected objects with focus on historical significance
        """
        if self.model is None:
            return ["Object detection unavailable - model not loaded"]
        
        try:
            # Convert PIL Image to format suitable for YOLO
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Run inference
            results = self.model(cv_image, verbose=False)
            
            # Extract detected objects
            detected_objects = []
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Get class name and confidence
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        class_name = self.model.names[class_id]
                        
                        # Only include objects with reasonable confidence
                        if confidence > 0.3:
                            # Focus on historically relevant objects
                            if self._is_historically_relevant(class_name):
                                detected_objects.append({
                                    'object': class_name,
                                    'confidence': round(confidence, 2)
                                })
            
            # Remove duplicates and sort by confidence
            unique_objects = {}
            for obj in detected_objects:
                obj_name = obj['object']
                if obj_name not in unique_objects or obj['confidence'] > unique_objects[obj_name]['confidence']:
                    unique_objects[obj_name] = obj
            
            # Sort by confidence and return object names
            sorted_objects = sorted(unique_objects.values(), key=lambda x: x['confidence'], reverse=True)
            
            # Return list of object names for historical analysis
            object_names = [obj['object'] for obj in sorted_objects]
            
            return object_names if object_names else ["No significant objects detected"]
        
        except Exception as e:
            print(f"Error during object detection: {str(e)}")
            return ["Error during object detection"]
    
    def _is_historically_relevant(self, class_name):
        """
        Check if detected object is relevant for historical analysis
        """
        # Objects that are commonly relevant in historical photos
        relevant_objects = {
            'person', 'people', 'man', 'woman', 'child',
            'car', 'truck', 'bus', 'motorcycle', 'bicycle',
            'horse', 'airplane', 'train', 'boat', 'ship',
            'building', 'house', 'church', 'tower',
            'flag', 'sign', 'banner',
            'uniform', 'hat', 'clothing',
            'weapon', 'gun', 'tank', 'military_vehicle',
            'crowd', 'group', 'gathering',
            'monument', 'statue', 'memorial',
            'bridge', 'road', 'street',
            'smoke', 'fire', 'explosion',
            'camera', 'microphone',
            'book', 'newspaper', 'document'
        }
        
        # Check if the detected class is in our relevant objects
        class_lower = class_name.lower()
        return any(relevant in class_lower for relevant in relevant_objects)
    
    def get_detailed_detections(self, image):
        """Get detailed detection information including bounding boxes"""
        if self.model is None:
            return []
        
        try:
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            results = self.model(cv_image, verbose=False)
            
            detailed_detections = []
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        class_name = self.model.names[class_id]
                        
                        if confidence > 0.3 and self._is_historically_relevant(class_name):
                            # Get bounding box coordinates
                            x1, y1, x2, y2 = box.xyxy[0].tolist()
                            
                            detailed_detections.append({
                                'object': class_name,
                                'confidence': round(confidence, 2),
                                'bbox': {
                                    'x1': int(x1), 'y1': int(y1),
                                    'x2': int(x2), 'y2': int(y2)
                                }
                            })
            
            return detailed_detections
        
        except Exception as e:
            print(f"Error getting detailed detections: {str(e)}")
            return []
