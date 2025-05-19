# Flask Webcam App

This project is a simple Flask web application that streams the webcam feed to a web page. It provides a clean and responsive GUI for users to view their webcam in real-time.

## Project Structure

```
flask-webcam-app
├── app.py               # Main entry point of the Flask application
├── requirements.txt     # Lists the dependencies required for the project
├── static
│   └── style.css        # CSS styles for the web application
├── templates
│   └── index.html       # HTML template for the main page
└── README.md            # Documentation for the project
```

## Setup Instructions

1. **Clone the repository**:
   ```
   git clone <repository-url>
   cd flask-webcam-app
   ```

2. **Create a virtual environment** (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the required dependencies**:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. **Run the Flask application**:
   ```
   python app.py
   ```

2. **Open your web browser** and navigate to `http://127.0.0.1:5000` to view the webcam feed.

## Notes

- Ensure that your webcam is connected and accessible by the application.
- You may need to adjust browser permissions to allow webcam access.