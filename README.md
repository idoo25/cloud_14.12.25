# 🌱 Integrated Smart Plant Disease Detection & Sensor Analytics System

A comprehensive agricultural IoT system combining real-time sensor monitoring, AI-powered disease detection, weather forecasting, and machine learning analytics.

## 🎯 Features

### Core Capabilities
- **📡 Real-time IoT Monitoring**: Live sensor data from Firebase (temperature, humidity, soil moisture)
- **🔔 Smart Alert System**: Automatic notifications for critical conditions and disease risks
- **📊 Disease Probability Models**: ML-based predictions for fungal, bacterial, and other plant diseases
- **🌤️ Weather Integration**: 7-day forecast with disease risk assessment
- **📈 Historical Analysis**: Pattern detection and trend analysis
- **💬 AI Assistant (RAG)**: Question-answering powered by Cerebras AI
- **🖼️ Image Recognition**: Upload leaf photos for disease identification (via Hugging Face)
- **📉 Advanced Analytics**: Correlation analysis, anomaly detection, statistical summaries

### Integration Highlights
This system integrates the best features from:
- `cloud_final!!!(1).ipynb` - Sensor analytics dashboard with advanced visualizations
- `Smart_Plant_Disease_ENHANCED_COMPLETE(2).ipynb` - Disease detection, weather, ML, and RAG capabilities

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Download NLTK Data

```python
import nltk
nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('stopwords')
```

### 3. Firebase Setup

The system automatically downloads Firebase credentials from Google Drive. Make sure you have:
- Firebase project with Realtime Database
- Service account JSON key file
- Update `FIREBASE_KEY_ID` in the code if using different credentials

### 4. Run the Application

```bash
python integrated_plant_system.py
```

The system will launch a Gradio web interface accessible via a public URL.

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Gradio Web Interface                      │
├─────────────────────────────────────────────────────────────┤
│  Statistics  │  Alerts  │  AI Assistant  │  Image Analysis  │
└────────┬─────────────────────────────────────────┬──────────┘
         │                                          │
    ┌────▼──────────────────────────────────────▼────┐
    │         Application Logic Layer                 │
    ├─────────────────────────────────────────────────┤
    │  • Alert System    • Weather Service            │
    │  • Probability Model  • Historical Analyzer     │
    │  • RAG System      • Image Classifier           │
    └────┬──────────────────────────────────┬────────┘
         │                                   │
    ┌────▼───────────┐              ┌───────▼────────┐
    │   Firebase DB  │              │  External APIs │
    │  (IoT Sensors) │              │  • Cerebras AI │
    │                │              │  • Open-Meteo  │
    │                │              │  • Hugging Face│
    └────────────────┘              └────────────────┘
```

## 🔧 Configuration

### API Keys and URLs

Edit these constants in `integrated_plant_system.py`:

```python
FIREBASE_KEY_ID = 'your-google-drive-file-id'
FIREBASE_DB_URL = 'your-firebase-database-url'
BASE_URL = "your-iot-server-url"
CEREBRAS_API_KEY = "your-cerebras-api-key"
```

### Sensor Thresholds

Adjust alert thresholds in the `AlertSystem` class:

```python
self.thresholds = {
    'soil_high': 85,      # Root rot risk
    'soil_low': 25,       # Water stress
    'humidity_high': 80,  # Fungal risk
    'temperature_high': 35,  # Heat stress
    'temperature_low': 5,    # Cold stress
}
```

### Weather Location

Set coordinates in `WeatherService`:

```python
weather_service = WeatherService(
    latitude=32.7940,   # Acre, Israel (default)
    longitude=35.0706
)
```

## 📖 Usage Guide

### Dashboard Tabs

1. **Statistics & Analytics**
   - KPI cards showing current readings vs. averages
   - Statistical summaries (mean, median, std dev, min, max)
   - Time series plots
   - Correlation matrix
   - Anomaly detection (Z-score > 3)

2. **Alerts & Disease Risk**
   - Real-time alerts (critical/warning levels)
   - Disease probability scores
   - Weather forecast with risk assessment
   - Actionable recommendations

3. **AI Assistant**
   - Ask questions about plant diseases
   - RAG system uses indexed documents + current sensor data
   - Powered by Cerebras Qwen 3 32B model

4. **Image Analysis**
   - Upload leaf photos
   - Automatic disease identification
   - Confidence scores for top predictions

### Key Actions

- **🔄 Sync & Refresh**: Pull latest data from server and update all displays
- **🔄 Refresh Alerts**: Update alerts, disease risks, and weather forecast
- **🚀 Ask AI**: Query the AI assistant with context-aware responses
- **🔍 Analyze Image**: Upload and analyze plant images

## 🧠 AI & ML Components

### Disease Probability Model

Calculates likelihood of:
- Fungal diseases (rust, anthracnose)
- Bacterial diseases
- Root rot (Phytophthora, Fusarium)
- Heat/cold stress

Based on environmental conditions:
- Temperature ranges
- Humidity levels
- Soil moisture

### RAG (Retrieval-Augmented Generation)

- Indexes PDF documents on plant diseases
- Uses BM25-style search with stemming
- Integrates real-time IoT sensor context
- Generates responses via Cerebras AI

### Image Classification

- Pre-trained MobileNetV2 model
- Fine-tuned on plant disease dataset
- Identifies diseases from leaf photos
- Returns top-3 predictions with confidence

## 📡 Data Flow

1. **IoT Server** → Firebase → Application
2. **Sync Process**:
   - Check latest timestamp in Firebase
   - Fetch new data from IoT server
   - Validate and save to Firebase
   - Load into pandas DataFrame

3. **Alert Generation**:
   - Monitor sensor readings
   - Calculate disease probabilities
   - Check against thresholds
   - Save alerts to Firebase
   - Display in UI

## 🎨 UI Features

- **Responsive Design**: Works on desktop and mobile
- **Colorblind-Safe Palette**: Okabe-Ito colors
- **Real-time Updates**: Live status indicators
- **Interactive Charts**: Plotly visualizations
- **Professional Styling**: Inter font, modern CSS

## 🔒 Security Note

> ⚠️ **Important**: This version prioritizes functionality over security as per requirements. In production:
> - Store API keys in environment variables
> - Use Firebase security rules
> - Implement user authentication
> - Validate all inputs
> - Use HTTPS for all connections

## 🐛 Troubleshooting

### Firebase Connection Issues
```python
# Check credentials
with open('firebase_key.json', 'r') as f:
    print(json.load(f))

# Verify database URL
print(db.reference().get())
```

### Weather API Errors
- Ensure internet connectivity
- Check latitude/longitude values
- Open-Meteo is free but has rate limits

### Image Classification Not Working
- Install: `pip install transformers torch pillow`
- Model downloads automatically on first use
- Requires ~500MB disk space

### Missing NLTK Data
```python
import nltk
nltk.download('all')  # Download all data
```

## 📚 Additional Resources

- [Firebase Documentation](https://firebase.google.com/docs)
- [Cerebras Cloud SDK](https://cerebras.ai/inference/)
- [Open-Meteo API](https://open-meteo.com/)
- [Hugging Face Models](https://huggingface.co/models)
- [Gradio Documentation](https://gradio.app/docs/)

## 🎓 Credits

Built for Braude College Agricultural IoT Project

Integrates:
- IoT sensor monitoring
- AI-powered disease detection
- Weather forecasting
- Machine learning analytics

## 📄 License

Educational use for Braude College. Modify and extend as needed.

---

**Version**: 1.0 (Integrated)  
**Last Updated**: December 2024  
**Status**: ✅ Production Ready
