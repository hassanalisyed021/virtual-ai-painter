import streamlit as st
import cv2
import numpy as np
import HandTrackingModule as htm
import time

class VirtualPainter:
    def __init__(self):
        # Get user input for brush and eraser thickness
        col1, col2 = st.columns(2)
        with col1:
            self.BRUSH_THICKNESS = st.slider("Brush Thickness", 1, 30, 15)
        with col2:
            self.ERASER_THICKNESS = st.slider("Eraser Thickness", 20, 100, 50)

        self.HEADER_HEIGHT = 125
        self.FRAME_WIDTH = 1280
        self.FRAME_HEIGHT = 720
        
        # Create canvas
        self.imgCanvas = np.zeros((self.FRAME_HEIGHT, self.FRAME_WIDTH, 3), np.uint8)
        
        # Load header images - simplified image loading
        self.headerImages = {
            'default': cv2.imread("PHOTO-2025-02-04-01-20-17.jpg"),
            'pink': cv2.imread("PHOTO-2025-02-04-01-20-37.jpg"),
            'blue': cv2.imread("PHOTO-2025-02-04-01-20-56.jpg"),
            'green': cv2.imread("PHOTO-2025-02-04-01-21-12.jpg"),
            'eraser': cv2.imread("PHOTO-2025-02-04-01-20-17.jpg")
        }
        
        # Resize header images
        for key in self.headerImages:
            if self.headerImages[key] is not None:
                self.headerImages[key] = cv2.resize(self.headerImages[key], (self.FRAME_WIDTH, self.HEADER_HEIGHT))
        
        self.currentHeader = 'default'
        
        # Color settings - adjusted blue color
        self.colors = {
            'pink': (255, 0, 255),
            'blue': (225, 105, 65),  # Changed back to bright blue
            'green': (0, 255, 0),
            'eraser': (0, 0, 0)
        }
        self.drawColor = self.colors['pink']
        
        # Drawing variables
        self.xp, self.yp = 0, 0
        
        # Initialize hand detector
        self.detector = htm.handDetector(detectionCon=0.85)
        
        # UI Elements
        self.colorZones = {
            'pink': (250, 450, 20, 100),
            'blue': (550, 750, 20, 100),
            'green': (800, 950, 20, 100),
            'eraser': (1050, 1200, 20, 100)
        }
        
        self.selectionOverlay = np.zeros((self.FRAME_HEIGHT, self.FRAME_WIDTH, 3), np.uint8)
        self.overlayAlpha = 0.3

    def create_selection_effect(self, x, y, color):
        cv2.circle(self.selectionOverlay, (x, y), 20, color, cv2.FILLED)
        self.selectionOverlay = np.zeros((self.FRAME_HEIGHT, self.FRAME_WIDTH, 3), np.uint8)

    def check_color_selection(self, x, y):
        for color, zone in self.colorZones.items():
            if zone[0] < x < zone[1] and zone[2] < y < zone[3]:
                self.drawColor = self.colors[color]
                self.currentHeader = color
                return True
        return False

    def draw(self, img, x1, y1):
        thickness = self.ERASER_THICKNESS if self.drawColor == (0, 0, 0) else self.BRUSH_THICKNESS
        
        if self.xp == 0 and self.yp == 0:
            self.xp, self.yp = x1, y1
            
        cv2.line(img, (self.xp, self.yp), (x1, y1), self.drawColor, thickness)
        cv2.line(self.imgCanvas, (self.xp, self.yp), (x1, y1), self.drawColor, thickness)
        
        if self.drawColor != (0, 0, 0):
            cv2.circle(img, (x1, y1), thickness//2, self.drawColor, cv2.FILLED)
            
        self.xp, self.yp = x1, y1

    def clear_canvas(self):
        self.imgCanvas = np.zeros((self.FRAME_HEIGHT, self.FRAME_WIDTH, 3), np.uint8)
        self.xp, self.yp = 0, 0  # Reset drawing points

def main():
    st.title("Virtual AI Painter")
    st.write("Use your hand to paint in real-time!")

    # Initialize the Virtual Painter
    if 'painter' not in st.session_state:
        st.session_state.painter = VirtualPainter()
    painter = st.session_state.painter

    # Create a placeholder for the video feed
    video_placeholder = st.empty()
    
    # Add control buttons
    col1, col2 = st.columns(2)
    with col1:
        start_button = st.button("Start/Stop Painting")
    with col2:
        if st.button("Clear Canvas"):
            painter.clear_canvas()

    if 'is_painting' not in st.session_state:
        st.session_state.is_painting = False

    if start_button:
        st.session_state.is_painting = not st.session_state.is_painting

    if st.session_state.is_painting:
        cap = cv2.VideoCapture(0)
        cap.set(3, painter.FRAME_WIDTH)
        cap.set(4, painter.FRAME_HEIGHT)

        while True:
            success, img = cap.read()
            if not success:
                st.error("Failed to access webcam")
                break

            img = cv2.flip(img, 1)
            
            # Find hand landmarks
            img = painter.detector.findHands(img)
            lmList, bbox = painter.detector.findPosition(img, draw=False)
            
            if lmList and len(lmList) >= 21:
                x1, y1 = lmList[8][1:]
                x2, y2 = lmList[12][1:]
                
                fingers = painter.detector.fingersUp()
                
                if fingers[1] and fingers[2]:
                    painter.xp, painter.yp = 0, 0
                    
                    if y1 < painter.HEADER_HEIGHT:
                        if painter.check_color_selection(x1, y1):
                            painter.create_selection_effect(x1, y1, painter.drawColor)
                            
                    cv2.circle(img, (x1, y1), 15, painter.drawColor, cv2.FILLED)
                    cv2.circle(img, (x2, y2), 15, painter.drawColor, cv2.FILLED)
                    cv2.line(img, (x1, y1), (x2, y2), painter.drawColor, 3)
                
                elif fingers[1] and not fingers[2]:
                    painter.draw(img, x1, y1)
            
            # Merge canvas and image
            imgGray = cv2.cvtColor(painter.imgCanvas, cv2.COLOR_BGR2GRAY)
            _, imgInv = cv2.threshold(imgGray, 50, 255, cv2.THRESH_BINARY_INV)
            imgInv = cv2.cvtColor(imgInv, cv2.COLOR_GRAY2BGR)
            img = cv2.bitwise_and(img, imgInv)
            img = cv2.bitwise_or(img, painter.imgCanvas)
            
            # Add header
            if painter.headerImages[painter.currentHeader] is not None:
                img[0:painter.HEADER_HEIGHT, 0:painter.FRAME_WIDTH] = painter.headerImages[painter.currentHeader]
            
            # Add selection overlay
            img = cv2.addWeighted(img, 1, painter.selectionOverlay, painter.overlayAlpha, 0)
            
            # Convert BGR to RGB for streamlit
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Display the image
            video_placeholder.image(img, channels="RGB", use_container_width=True)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main() 