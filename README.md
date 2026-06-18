# AI Real-time Gym Coach

A Streamlit web app that uses live webcam pose detection to track workouts, count reps and sets, surface form metrics, and provide short AI voice coaching cues during a training session.

## Features

- Username-based login with local user history
- Real-time webcam workout analysis through `streamlit-webrtc`
- Pose landmark detection with MediaPipe
- Rep, set, and workout-time tracking
- Exercise-specific form metrics for:
  - Push-ups
  - Squats
  - Lunges
  - Shoulder Press
- AI coaching feedback powered by Groq
- Text-to-speech playback for coaching prompts
- Local SQLite workout history stored in `data.db`
- Custom Streamlit styling and local font support

## Tech Stack

- Python
- Streamlit
- streamlit-webrtc
- MediaPipe
- OpenCV
- Pandas
- SQLite
- Groq API
- gTTS

## Project Structure

```text
gymtrainingapp/
|-- core/                  # Shared exercise base logic
|-- detectors/             # Exercise-specific pose analysis
|-- ml_models/             # MediaPipe pose landmarker model
|-- services/
|   |-- auth/              # Login wall
|   |-- coaching/          # LLM, TTS, and voice coaching pipeline
|   |-- config/            # Exercise options and prompt config
|   |-- persistence/       # SQLite repository
|   |-- state/             # Streamlit session defaults
|   |-- tracking/          # Workout metric syncing
|   |-- ui/                # CSS/font injection helpers
|   `-- vision/            # WebRTC video processor
|-- static/                # CSS and font assets
|-- main.py                # Streamlit app entry point
|-- requirements.txt       # Python dependencies
`-- data.db                # Local SQLite database
```

## Setup

### 1. Create a virtual environment

```bash
python -m venv myenv
```

Activate it:

```bash
# Windows
myenv\Scripts\activate

# macOS/Linux
source myenv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file or add Streamlit secrets for Groq:

```env
GROQ_API_KEY=your_groq_api_key_here
```

You can also place the key in `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY = "your_groq_api_key_here"
```

The app can still load without a key, but AI voice coaching requires a valid Groq API key.

## Run the App

```bash
streamlit run main.py
```

Then open the local Streamlit URL shown in the terminal.

## How to Use

1. Enter a unique username on the login screen.
2. Choose an exercise, number of sets, and reps per set in the sidebar.
3. Click **Start Session**.
4. Allow camera access in your browser.
5. Perform the exercise in view of the camera.
6. Watch the live workout metrics and listen for coaching feedback.
7. End the workout to return to planning mode.
8. Review previous workout totals in the workout history table.

## Notes

- The database is local and stored in `data.db`.
- Webcam access is required for real-time pose detection.
- Good lighting and a full-body camera view improve pose tracking accuracy.
- The app currently lists `Planks` in the workout selector, but the visible metric panels and detector files focus on push-ups, squats, lunges, biceps curls, and shoulder press.

## Development

Run a quick syntax check:

```bash
python -m py_compile main.py
```

Recommended cleanup before sharing or deploying:

- Keep `.env`, `.streamlit/secrets.toml`, `data.db`, `__pycache__/`, and virtual environment folders out of version control.
- Add any new detector to `detectors/`, wire it into the video processor, and add matching metric defaults in `services/config/workout_config.py`.
