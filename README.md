# Virtual AI Painter

I have created a **Virtual AI Painter**, a real-time hand-tracking drawing application using OpenCV and Streamlit. Instead of using a traditional mouse or touchscreen, you can use hand gestures to paint dynamically.

 - ![Alt text](painter.gif)

## Features
- **Hand Tracking**: Uses a hand-tracking module to detect hand movements.
- **Brush & Eraser**: Adjustable brush thickness and an eraser mode.
- **Color Selection**: Switch between different colors using hand gestures.
- **Live Drawing**: Real-time video feed with dynamic drawing interactions.
- **Streamlit UI**: Simple web-based interface for control.

## Installation
1. Clone the repository:
   ```sh
   https://github.com/hassanalisyed021/virtual-ai-painter.git
   cd virtual-ai-painter
   ```
   
2. Ensure you have **OpenCV** and **Streamlit** installed:
   ```sh
   pip install opencv-python numpy mediapipe
   ```

## Usage
Run the application:
```sh
streamlit run streamlit_painter.py
```
Now, you can use hand gestures to draw on the virtual canvas in real-time!

## License
This project is open-source. Feel free to modify and improve it!


