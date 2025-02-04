import cv2
import numpy as np
import os
import HandTrackingModule as htm

class VirtualPainter:
    def __init__(self):
        self.BRUSH_THICKNESS = 15
        self.ERASER_THICKNESS = 50
        self.HEADER_HEIGHT = 125
        
        # Initialize camera
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, 1280)
        self.cap.set(4, 720)
        
        # Create canvas
        self.imgCanvas = np.zeros((720, 1280, 3), np.uint8)
        
        # Load header images with the exact filenames you provided
        self.headerImages = {
            'default': self.load_header_image("PHOTO-2025-02-04-01-20-17.jpg"),
            'pink': self.load_header_image("PHOTO-2025-02-04-01-20-37.jpg"),
            'blue': self.load_header_image("PHOTO-2025-02-04-01-20-56.jpg"),
            'green': self.load_header_image("PHOTO-2025-02-04-01-21-12.jpg"),
            'eraser': self.load_header_image("Screenshot 2025-02-04 at 2.17.21 AM.png")
        }
        
        # Current header
        self.currentHeader = 'default'
        
        # Color settings
        self.colors = {
            'pink': (255, 0, 255),
            'blue': (165, 42, 42),
            'green': (0, 255, 0),
            'eraser': (0, 0, 0)
        }
        self.drawColor = self.colors['pink']
        
        # Drawing variables
        self.xp, self.yp = 0, 0
        
        # Initialize hand detector
        self.detector = htm.handDetector(detectionCon=0.85)
        
        # UI Elements - Adjusted to match your header image
        self.colorZones = {
            'pink': (250, 450, 20, 100),    # x1, x2, y1, y2
            'blue': (550, 750, 20, 100),
            'green': (800, 950, 20, 100),
            'eraser': (1050, 1200, 20, 100)
        }
        
        # Selection animation
        self.selectionOverlay = np.zeros((720, 1280, 3), np.uint8)
        self.overlayAlpha = 0.3
        
    def load_header_image(self, filename):
        # Try to load image from current directory first
        img = cv2.imread(filename)
        if img is None:
            # If not found, try loading from project root
            img = cv2.imread(os.path.join(os.path.dirname(__file__), filename))
        
        if img is not None:
            return cv2.resize(img, (1280, self.HEADER_HEIGHT))
        print(f"Warning: Could not load image {filename}")
        return None

    def create_selection_effect(self, x, y, color):
        cv2.circle(self.selectionOverlay, (x, y), 20, color, cv2.FILLED)
        self.selectionOverlay = np.zeros((720, 1280, 3), np.uint8)

    def check_color_selection(self, x, y):
        for color, zone in self.colorZones.items():
            if zone[0] < x < zone[1] and zone[2] < y < zone[3]:
                self.drawColor = self.colors[color]
                self.currentHeader = color
                return True
        return False

    def draw(self, img, x1, y1, mode='draw'):
        if mode == 'draw':
            thickness = self.ERASER_THICKNESS if self.drawColor == (0, 0, 0) else self.BRUSH_THICKNESS
            
            if self.xp == 0 and self.yp == 0:
                self.xp, self.yp = x1, y1
                
            cv2.line(img, (self.xp, self.yp), (x1, y1), self.drawColor, thickness)
            cv2.line(self.imgCanvas, (self.xp, self.yp), (x1, y1), self.drawColor, thickness)
            
            # Add drawing effect
            if self.drawColor != (0, 0, 0):  # Not eraser
                cv2.circle(img, (x1, y1), thickness//2, self.drawColor, cv2.FILLED)
                
            self.xp, self.yp = x1, y1

    def run(self):
        while True:
            success, img = self.cap.read()
            if not success:
                continue
                
            img = cv2.flip(img, 1)
            
            # Find hand landmarks
            img = self.detector.findHands(img)
            lmList, bbox = self.detector.findPosition(img, draw=False)
            
            if lmList and len(lmList) >= 21:
                x1, y1 = lmList[8][1:]  # Index finger tip
                x2, y2 = lmList[12][1:]  # Middle finger tip
                
                fingers = self.detector.fingersUp()
                
                # Selection Mode - Two fingers up
                if fingers[1] and fingers[2]:
                    self.xp, self.yp = 0, 0
                    
                    if y1 < self.HEADER_HEIGHT:
                        if self.check_color_selection(x1, y1):
                            self.create_selection_effect(x1, y1, self.drawColor)
                            
                    cv2.circle(img, (x1, y1), 15, self.drawColor, cv2.FILLED)
                    cv2.circle(img, (x2, y2), 15, self.drawColor, cv2.FILLED)
                    cv2.line(img, (x1, y1), (x2, y2), self.drawColor, 3)
                
                # Drawing Mode - Index finger up only
                elif fingers[1] and not fingers[2]:
                    self.draw(img, x1, y1)
            
            # Merge canvas and image
            imgGray = cv2.cvtColor(self.imgCanvas, cv2.COLOR_BGR2GRAY)
            _, imgInv = cv2.threshold(imgGray, 50, 255, cv2.THRESH_BINARY_INV)
            imgInv = cv2.cvtColor(imgInv, cv2.COLOR_GRAY2BGR)
            img = cv2.bitwise_and(img, imgInv)
            img = cv2.bitwise_or(img, self.imgCanvas)
            
            # Add header
            if self.headerImages[self.currentHeader] is not None:
                img[0:self.HEADER_HEIGHT, 0:1280] = self.headerImages[self.currentHeader]
            
            # Add selection overlay
            img = cv2.addWeighted(img, 1, self.selectionOverlay, self.overlayAlpha, 0)
            
            cv2.imshow("Virtual Painter", img)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    painter = VirtualPainter()
    painter.run()