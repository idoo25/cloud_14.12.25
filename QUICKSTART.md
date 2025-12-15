# 🚀 Quick Start Guide

Get the Integrated Smart Plant Disease Detection System running in minutes!

## ⚡ Super Quick Start (Linux/Mac)

```bash
# 1. Clone and enter directory
cd /path/to/cloud_14.12.25

# 2. Run the launcher
./run.sh
```

That's it! The system will:
- Check dependencies and install if needed
- Download NLTK data
- Launch the Gradio interface

## 🪟 Windows Quick Start

```cmd
# 1. Install dependencies
pip install -r requirements.txt

# 2. Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab'); nltk.download('stopwords')"

# 3. Run the application
python integrated_plant_system.py
```

## 🌐 Access the Application

After launching, you'll see output like:

```
🌱 INTEGRATED SMART PLANT DISEASE DETECTION & SENSOR ANALYTICS SYSTEM
================================================================================
📥 Downloading Firebase credentials...
✓ Project: cloud-81451
✓ Firebase initialized
🚀 Initializing system...
📥 Loading data...
✓ Loaded 1234 records
✅ System ready!

Running on local URL:  http://127.0.0.1:7860
Running on public URL: https://xxxxxxxxxxxxx.gradio.live
```

Open the public URL in your browser to access the dashboard from anywhere!

## 📱 Using the Dashboard

### 1️⃣ Statistics & Analytics Tab
- View real-time sensor readings (Temperature, Humidity, Soil Moisture)
- See statistical summaries and KPI cards
- Explore time series plots
- Check correlation matrix
- Review detected anomalies

**Actions:**
- Click **🔄 Sync & Refresh** to pull latest data from the IoT server

### 2️⃣ Alerts & Disease Risk Tab
- Monitor active alerts (critical and warnings)
- Check disease probability scores
- Review 7-day weather forecast with disease risk

**Actions:**
- Click **🔄 Refresh Alerts** to update risk assessment

### 3️⃣ AI Assistant Tab
- Ask questions about plant diseases and agriculture
- Get AI-powered answers using RAG (Retrieval-Augmented Generation)
- Context includes current sensor readings

**Example Questions:**
- "What diseases affect fig plants?"
- "How can I prevent fungal infections?"
- "What are the symptoms of root rot?"

**Actions:**
- Type question → Set number of sources → Click **🚀 Ask AI**

### 4️⃣ Image Analysis Tab
- Upload photos of plant leaves
- Get automatic disease identification
- See confidence scores for top predictions

**Actions:**
- Upload image → Click **🔍 Analyze Image**

## 🔧 Configuration

### Change Location for Weather
Edit `integrated_plant_system.py`:

```python
weather_service = WeatherService(
    latitude=YOUR_LATITUDE,   # e.g., 32.7940
    longitude=YOUR_LONGITUDE  # e.g., 35.0706
)
```

### Adjust Alert Thresholds
Edit the `AlertSystem` class:

```python
self.thresholds = {
    'soil_high': 85,          # Adjust as needed
    'soil_low': 25,
    'humidity_high': 80,
    'temperature_high': 35,
    'temperature_low': 5,
}
```

## 🐛 Common Issues

### Issue: "Firebase credentials not found"
**Solution:** 
- Ensure internet connection for auto-download
- Check `FIREBASE_KEY_ID` is correct
- Manually place `firebase_key.json` in the directory

### Issue: "Image classification not available"
**Solution:**
```bash
pip install transformers torch pillow
```

### Issue: "NLTK data missing"
**Solution:**
```python
import nltk
nltk.download('all')
```

### Issue: "Module not found"
**Solution:**
```bash
pip install -r requirements.txt --upgrade
```

## 📊 Understanding the Data

### Sensor Readings
- **Temperature**: °C, typically 15-35°C
- **Humidity**: %, typically 40-90%
- **Soil Moisture**: %, typically 20-80%

### Alert Levels
- 🟢 **Normal**: All conditions within safe ranges
- 🟡 **Warning**: Monitoring required
- 🔴 **Critical**: Immediate action needed

### Disease Risk Scores
- **0-25**: Low risk
- **25-50**: Moderate risk
- **50-75**: High risk
- **75-100**: Critical risk

## 🎯 Best Practices

1. **Regular Monitoring**
   - Sync data every 30-60 minutes
   - Check alerts daily
   - Review trends weekly

2. **Disease Prevention**
   - Act on alerts immediately
   - Monitor weather forecasts
   - Inspect plants when risk is high

3. **Data Quality**
   - Verify sensor readings are realistic
   - Check for anomalies
   - Ensure sensors are calibrated

## 🆘 Getting Help

### Check Logs
The application prints status messages to console:
```
✓ Success messages
⚠️ Warning messages
❌ Error messages
```

### Verify Setup
```bash
# Test Python
python3 --version  # Should be 3.8+

# Test dependencies
python3 -c "import gradio; import firebase_admin; print('OK')"

# Test Firebase
python3 -c "import firebase_admin; print('Firebase installed')"
```

### Read Documentation
- `README.md` - Comprehensive documentation
- `INTEGRATION_NOTES.md` - Technical details
- This file - Quick start guide

## 🎓 Next Steps

Once everything is running:

1. **Explore the Dashboard**: Click through all tabs
2. **Test Features**: Upload an image, ask the AI questions
3. **Customize Settings**: Adjust thresholds and location
4. **Add Documents**: Place PDF files in the directory and modify code to index them
5. **Monitor Regularly**: Set up a routine for checking alerts

## 📞 Support

For Braude College Agricultural IoT Project:
- Check the README for detailed documentation
- Review INTEGRATION_NOTES for technical details
- Consult the code comments for specific functions

---

**Happy Monitoring! 🌱**
