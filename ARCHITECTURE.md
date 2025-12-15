# 🏗️ System Architecture

## Overview

The integrated system combines IoT monitoring, AI-powered disease detection, and advanced analytics into a unified platform.

## 📐 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER INTERFACE (Gradio)                      │
│                    https://xxx.gradio.live                       │
├──────────────┬──────────────┬──────────────┬───────────────────┤
│ Statistics & │  Alerts &    │ AI Assistant │ Image Analysis    │
│  Analytics   │ Disease Risk │    (RAG)     │  (Hugging Face)   │
└──────┬───────┴──────┬───────┴──────┬───────┴───────┬───────────┘
       │              │              │               │
       └──────────────┴──────────────┴───────────────┘
                       │
       ┌───────────────▼────────────────────────────────────┐
       │          APPLICATION LAYER (Python)                 │
       │         integrated_plant_system.py                  │
       ├─────────────────────────────────────────────────────┤
       │  Core Services:                                     │
       │  • WeatherService          • AlertSystem            │
       │  • DiseaseProbabilityModel • HistoricalAnalyzer     │
       │  • PlantDiseaseRAG         • ImageClassifier        │
       │  • Firebase Sync           • Data Processing        │
       └──┬──────────┬──────────┬──────────┬────────────────┘
          │          │          │          │
    ┌─────▼──┐  ┌───▼────┐  ┌──▼──────┐  ┌▼────────────┐
    │Firebase│  │Cerebras│  │Open-    │  │Hugging Face │
    │  DB    │  │  AI    │  │Meteo    │  │   Models    │
    │(Sensor)│  │ (RAG)  │  │(Weather)│  │  (Images)   │
    └────────┘  └────────┘  └─────────┘  └─────────────┘
```

## 🔧 Component Details

### 1. Firebase Integration
```
IoT Server → Firebase Realtime DB → Application
                    ↓
    Stores: sensor_data/
            └── timestamp-key
                ├── temperature
                ├── humidity
                ├── soil
                └── created_at
            
            alerts/
            └── timestamp-key
                ├── level (CRITICAL/WARNING)
                ├── type
                ├── message
                └── action
```

### 2. Data Flow
```
┌──────────────┐
│  IoT Sensors │ (Temperature, Humidity, Soil)
└──────┬───────┘
       │ HTTP POST
┌──────▼────────┐
│  IoT Server   │ (server-cloud-v645.onrender.com)
└──────┬────────┘
       │ REST API
┌──────▼────────┐
│   Firebase    │ (Realtime Database)
└──────┬────────┘
       │ SDK
┌──────▼─────────────────────────────────────┐
│ Application (integrated_plant_system.py)   │
│                                             │
│ Sync Process:                               │
│ 1. get_latest_timestamp_from_firebase()     │
│ 2. fetch_batch_from_server()                │
│ 3. save_to_firebase(new_data)              │
│ 4. load_data_from_firebase()               │
└──────┬──────────────────────────────────────┘
       │
┌──────▼────────┐
│  UI Display   │ (Gradio Dashboard)
└───────────────┘
```

### 3. Alert System Flow
```
Sensor Data → Disease Model → Risk Score → Alert Check
                    ↓              ↓            ↓
              Probability    Weather API   Threshold
              Calculation    Integration   Comparison
                    ↓              ↓            ↓
                    └──────────────┴────────────┘
                                   │
                         ┌─────────▼──────────┐
                         │  Alert Generation   │
                         │  • Level (Crit/Warn)│
                         │  • Type             │
                         │  • Message          │
                         │  • Action           │
                         └─────────┬───────────┘
                                   │
                         ┌─────────▼───────────┐
                         │ Save to Firebase    │
                         │ Display in UI       │
                         └─────────────────────┘
```

### 4. RAG System Architecture
```
┌──────────────────────────────────────────────────┐
│             RAG Query Process                     │
└──────────────────────────────────────────────────┘
                       │
      ┌────────────────┴──────────────────┐
      │                                    │
┌─────▼──────┐                    ┌───────▼────────┐
│  User      │                    │ Current Sensor │
│  Question  │                    │    Context     │
└─────┬──────┘                    └───────┬────────┘
      │                                   │
      └────────────────┬──────────────────┘
                       │
            ┌──────────▼──────────┐
            │ PlantDiseaseIndexer │
            │ • Preprocess query  │
            │ • Tokenize & stem   │
            │ • Search index      │
            └──────────┬──────────┘
                       │
            ┌──────────▼──────────┐
            │ Retrieve Top-K      │
            │ Relevant Chunks     │
            └──────────┬──────────┘
                       │
            ┌──────────▼──────────┐
            │ Build Context       │
            │ Sources + IoT data  │
            └──────────┬──────────┘
                       │
            ┌──────────▼──────────┐
            │   Cerebras AI API   │
            │   (Qwen 3 32B)      │
            └──────────┬──────────┘
                       │
            ┌──────────▼──────────┐
            │  Generated Answer   │
            │  with Citations     │
            └─────────────────────┘
```

### 5. Disease Probability Model
```
Input: Temperature, Humidity, Soil Moisture
              │
    ┌─────────┴─────────┐
    │                   │
┌───▼──────────┐  ┌────▼────────────┐
│Fungal Disease│  │Bacterial Disease│
│Conditions:   │  │Conditions:      │
│• Hum > 70%   │  │• Hum > 85%      │
│• 20-30°C     │  │• 25-35°C        │
└───┬──────────┘  └────┬────────────┘
    │                  │
    └──────────┬───────┘
               │
    ┌──────────▼───────────┐
    │  Calculate Scores    │
    │  (0-100 for each)    │
    └──────────┬───────────┘
               │
    ┌──────────▼───────────┐
    │  Rank by Probability │
    │  Return Top Risk     │
    └──────────────────────┘
```

### 6. Weather Integration
```
┌───────────────────┐
│ WeatherService    │
│ (Open-Meteo API)  │
└─────────┬─────────┘
          │
    ┌─────┴──────┐
    │            │
┌───▼────────┐   ┌▼─────────────┐
│ Current    │   │ 7-Day        │
│ Weather    │   │ Forecast     │
│ • Temp     │   │ • Temp range │
│ • Humidity │   │ • Rain prob  │
│ • Rain     │   │ • Precip     │
└───┬────────┘   └┬─────────────┘
    │             │
    └──────┬──────┘
           │
    ┌──────▼────────────┐
    │ Disease Risk      │
    │ Prediction        │
    │ • High rain → +30 │
    │ • Heat → +20      │
    │ • Wet period → +25│
    └──────┬────────────┘
           │
    ┌──────▼────────────┐
    │ Risk Level        │
    │ 🔴 HIGH (≥50)    │
    │ 🟡 MODERATE (≥25)│
    │ 🟢 LOW (<25)     │
    └───────────────────┘
```

## 🎨 UI Component Structure

```
┌─────────────────────────────────────────────────────────┐
│                    Gradio Blocks                         │
├─────────────────────────────────────────────────────────┤
│  Header: Title, Status Badge, Data Info                 │
├─────────────────────────────────────────────────────────┤
│  Controls: Sync & Refresh Button, Status Box            │
├─────────────────────────────────────────────────────────┤
│  KPI Cards: [Temperature] [Humidity] [Soil Moisture]    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────────────────────────────┐     │
│  │ Tab 1: Statistics & Analytics                  │     │
│  │ • Statistics Cards (Mean, Median, Std, etc.)   │     │
│  │ • Time Series Plot                             │     │
│  │ • Correlation Matrix                           │     │
│  │ • Anomaly Table                                │     │
│  └────────────────────────────────────────────────┘     │
│                                                          │
│  ┌────────────────────────────────────────────────┐     │
│  │ Tab 2: Alerts & Disease Risk                   │     │
│  │ • Active Alerts Display                        │     │
│  │ • Disease Probabilities                        │     │
│  │ • Weather Forecast                             │     │
│  │ • Refresh Button                               │     │
│  └────────────────────────────────────────────────┘     │
│                                                          │
│  ┌────────────────────────────────────────────────┐     │
│  │ Tab 3: AI Assistant                            │     │
│  │ • Question Input Box                           │     │
│  │ • Parameters (Sources, Temperature)            │     │
│  │ • Ask Button                                   │     │
│  │ • Answer Display                               │     │
│  └────────────────────────────────────────────────┘     │
│                                                          │
│  ┌────────────────────────────────────────────────┐     │
│  │ Tab 4: Image Analysis                          │     │
│  │ • Image Upload Box                             │     │
│  │ • Analyze Button                               │     │
│  │ • Results Display                              │     │
│  └────────────────────────────────────────────────┘     │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## 📊 Data Models

### Sensor Data Model
```python
{
    "timestamp": datetime,       # When reading was taken
    "temperature": float,        # -50 to 100°C
    "humidity": float,          # 0 to 100%
    "soil": float              # 0 to 100%
}
```

### Alert Model
```python
{
    "level": str,              # "CRITICAL" or "WARNING"
    "type": str,               # Alert category
    "message": str,            # Human-readable message
    "value": float,            # Sensor reading
    "threshold": float,        # Threshold exceeded
    "action": str,             # Recommended action
    "timestamp": str           # ISO format
}
```

### Disease Probability Model
```python
{
    "all": {
        "fungal": {"name": str, "probability": float},
        "bacterial": {"name": str, "probability": float},
        "root_rot": {"name": str, "probability": float},
        "heat_stress": {"name": str, "probability": float}
    },
    "top_risk": {
        "disease": str,
        "probability": float
    }
}
```

## 🔄 State Management

```
Application State:
├── df (DataFrame)              # Current sensor data
├── weather_service             # Weather API client
├── alert_system                # Alert manager
├── prob_model                  # Disease calculator
├── historical_analyzer         # Pattern detector
├── image_classifier            # ML model
├── rag                         # AI assistant
└── indexer                     # Document index

UI State (Gradio):
├── sync_status (Textbox)       # Sync messages
├── data_info (Markdown)        # Data summary
├── kpi_outputs (HTML list)     # KPI cards
├── plots (Plot objects)        # Visualizations
├── tables (Dataframe objects)  # Data tables
└── displays (Markdown objects) # Text content
```

## 🚀 Execution Flow

### Application Startup
```
1. Import libraries
2. Initialize Firebase
3. Create Cerebras client
4. Load WeatherService
5. Initialize AlertSystem
6. Create DiseaseProbabilityModel
7. Load HistoricalAnalyzer
8. Initialize ImageClassifier (if available)
9. Create RAG system (Indexer + RAG)
10. Sync initial data
11. Build Gradio interface
12. Launch web server
```

### User Interaction Flow
```
User Action → Event Handler → Process Data → Update State → Refresh UI
     │             │               │              │            │
     └─────────────┴───────────────┴──────────────┴────────────┘
                            │
                    Return Results
```

## 🔐 Security Considerations

Current Implementation (as requested):
- ❌ API keys in source code
- ❌ No authentication
- ❌ Public Gradio interface
- ❌ Direct database access

Production Recommendations:
- ✅ Environment variables for secrets
- ✅ User authentication (Firebase Auth)
- ✅ Database security rules
- ✅ HTTPS only
- ✅ Rate limiting
- ✅ Input validation

## 📈 Performance Optimizations

1. **Data Loading**: Single Firebase query, cached in memory
2. **Event Handlers**: Only update necessary components
3. **Plotting**: Reuse styling function, optimize data points
4. **ML Models**: Lazy loading, optional dependencies
5. **API Calls**: Timeout settings, error handling

## 🛠️ Extensibility Points

Easy to extend:
- Add new disease types (DiseaseProbabilityModel)
- Add more alert thresholds (AlertSystem)
- Index more documents (PlantDiseaseIndexer)
- Add new visualizations (plot functions)
- Integrate more APIs (weather, satellite, etc.)
- Add new tabs (reports, settings, etc.)

## 📚 Module Dependencies

```
integrated_plant_system.py
├── Core Dependencies (Required)
│   ├── cerebras-cloud-sdk
│   ├── firebase-admin
│   ├── gradio
│   ├── plotly
│   ├── pandas
│   ├── numpy
│   ├── nltk
│   └── PyPDF2
│
├── ML Dependencies (Optional)
│   ├── transformers
│   ├── torch
│   ├── scikit-learn
│   └── xgboost
│
└── Report Dependencies (Optional)
    └── python-docx
```

---

**Last Updated**: December 15, 2024  
**Architecture Version**: 1.0  
**Status**: Production Ready
