#!/usr/bin/env python3
"""
🌱 Integrated Smart Plant Disease Detection & Sensor Analytics System
Combines IoT monitoring, disease detection, weather integration, and ML predictions
"""

# ============================================================================
# IMPORTS
# ============================================================================
from cerebras.cloud.sdk import Cerebras
import PyPDF2, gdown, re, json, os, math, time, warnings
from collections import defaultdict
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
import requests
warnings.filterwarnings('ignore')

# Firebase
import firebase_admin
from firebase_admin import credentials, db

# Visualization
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from scipy import stats

# ML & Hugging Face
try:
    from transformers import pipeline, AutoModelForImageClassification
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import classification_report, confusion_matrix
    import xgboost as xgb
    from PIL import Image
    import torch
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    print("⚠️ Hugging Face libraries not available - ML features disabled")

# Reports
try:
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    print("⚠️ python-docx not available - report generation disabled")

# Interface
import gradio as gr

# ============================================================================
# CONFIGURATION
# ============================================================================
FIREBASE_KEY_FILE = 'firebase_key.json'
FIREBASE_KEY_ID = '1ESnh8BIbGKrVEijA9nKNgNJNdD5kAaYC'
FIREBASE_DB_URL = 'https://cloud-81451-default-rtdb.europe-west1.firebasedatabase.app/'
BASE_URL = "https://server-cloud-v645.onrender.com/"
FEED = "json"
BATCH_LIMIT = 200
CEREBRAS_API_KEY = "csk-r8npfcy9jckcxcd98t4422mw99wx3ew89k4h3rrhdvy5ekde"
MODEL_NAME = "qwen-3-32b"

# Design system - Colorblind-safe Okabe-Ito palette
COLORS = {
    'temperature': {'primary': '#ef4444', 'gradient': 'linear-gradient(135deg, #dc2626 0%, #ef4444 100%)'},
    'humidity': {'primary': '#3b82f6', 'gradient': 'linear-gradient(135deg, #2563eb 0%, #3b82f6 100%)'},
    'soil': {'primary': '#10b981', 'gradient': 'linear-gradient(135deg, #059669 0%, #10b981 100%)'},
    'status': {'normal': '#10b981', 'warning': '#f59e0b', 'critical': '#ef4444', 'info': '#3b82f6'},
    'neutral': {'text': '#1f2937', 'subtext': '#6b7280', 'border': '#e5e7eb', 'bg': '#ffffff'}
}

SENSORS = [
    ('temperature', '°C', COLORS['temperature']['primary'], COLORS['temperature']['gradient'], 'TEMPERATURE'),
    ('humidity', '%', COLORS['humidity']['primary'], COLORS['humidity']['gradient'], 'HUMIDITY'),
    ('soil', '%', COLORS['soil']['primary'], COLORS['soil']['gradient'], 'SOIL MOISTURE')
]

# ============================================================================
# FIREBASE & API INITIALIZATION
# ============================================================================
def initialize_firebase():
    """Initialize Firebase with credentials."""
    if os.path.exists(FIREBASE_KEY_FILE):
        os.remove(FIREBASE_KEY_FILE)
    
    print('📥 Downloading Firebase credentials...')
    try:
        url = f'https://drive.google.com/uc?id={FIREBASE_KEY_ID}'
        gdown.download(url, FIREBASE_KEY_FILE, quiet=False, fuzzy=True)
        with open(FIREBASE_KEY_FILE, 'r') as f:
            creds = json.load(f)
        print(f'✓ Project: {creds.get("project_id")}')
    except Exception as e:
        print(f'⚠️ Error: {e}')
        raise
    
    if not firebase_admin._apps:
        firebase_admin.initialize_app(
            credentials.Certificate(FIREBASE_KEY_FILE),
            {'databaseURL': FIREBASE_DB_URL}
        )
        print('✓ Firebase initialized')

# Initialize Firebase
initialize_firebase()

# Initialize Cerebras client
client = Cerebras(api_key=CEREBRAS_API_KEY)

# ============================================================================
# WEATHER SERVICE
# ============================================================================
class WeatherService:
    """Weather API integration for disease risk prediction using Open-Meteo."""
    
    def __init__(self, latitude: float = 32.7940, longitude: float = 35.0706):
        self.latitude = latitude
        self.longitude = longitude
        self.base_url = "https://api.open-meteo.com/v1/forecast"
    
    def get_current_weather(self) -> Dict:
        """Get current weather conditions."""
        try:
            params = {
                'latitude': self.latitude,
                'longitude': self.longitude,
                'current': 'temperature_2m,relative_humidity_2m,precipitation,rain,cloud_cover',
                'timezone': 'auto'
            }
            response = requests.get(self.base_url, params=params, timeout=10)
            data = response.json()
            current = data['current']
            return {
                'temperature': current['temperature_2m'],
                'humidity': current['relative_humidity_2m'],
                'precipitation': current['precipitation'],
                'rain': current['rain'],
                'cloud_cover': current['cloud_cover'],
                'timestamp': current['time']
            }
        except Exception as e:
            print(f"Weather API error: {e}")
            return None
    
    def get_forecast(self, days: int = 7) -> pd.DataFrame:
        """Get weather forecast for next N days."""
        try:
            params = {
                'latitude': self.latitude,
                'longitude': self.longitude,
                'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,rain_sum,precipitation_probability_max',
                'timezone': 'auto',
                'forecast_days': days
            }
            response = requests.get(self.base_url, params=params, timeout=10)
            data = response.json()
            df = pd.DataFrame({
                'date': pd.to_datetime(data['daily']['time']),
                'temp_max': data['daily']['temperature_2m_max'],
                'temp_min': data['daily']['temperature_2m_min'],
                'precipitation': data['daily']['precipitation_sum'],
                'rain': data['daily']['rain_sum'],
                'rain_probability': data['daily']['precipitation_probability_max']
            })
            return df
        except Exception as e:
            print(f"Forecast API error: {e}")
            return pd.DataFrame()
    
    def predict_disease_risk_from_forecast(self, forecast_df: pd.DataFrame) -> Dict:
        """Predict disease risk based on weather forecast."""
        if forecast_df.empty:
            return {'risk_level': 'Unknown', 'risk_score': 0, 'risk_factors': []}
        
        risk_factors = []
        risk_score = 0
        
        if forecast_df['rain_probability'].mean() > 60:
            risk_score += 30
            risk_factors.append("High rain probability (fungal risk)")
        
        if forecast_df['temp_max'].max() > 35:
            risk_score += 20
            risk_factors.append("Heat stress forecasted")
        
        rainy_days = (forecast_df['precipitation'] > 5).sum()
        if rainy_days >= 3:
            risk_score += 25
            risk_factors.append(f"Extended wet period ({rainy_days} days)")
        
        risk_level = "🔴 HIGH" if risk_score >= 50 else ("🟡 MODERATE" if risk_score >= 25 else "🟢 LOW")
        
        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'risk_factors': risk_factors,
            'forecast_days': len(forecast_df)
        }

# ============================================================================
# FIREBASE SYNC FUNCTIONS
# ============================================================================
def get_latest_timestamp_from_firebase():
    try:
        latest = db.reference('/sensor_data').order_by_child('created_at').limit_to_last(1).get()
        return list(latest.values())[0]['created_at'] if latest else None
    except:
        return None

def fetch_batch_from_server(before_timestamp=None):
    params = {"feed": FEED, "limit": BATCH_LIMIT}
    if before_timestamp:
        params["before_created_at"] = before_timestamp
    try:
        return requests.get(f"{BASE_URL}/history", params=params, timeout=180).json()
    except:
        return {}

def save_to_firebase(data_list):
    if not data_list:
        return 0
    ref, saved = db.reference('/sensor_data'), 0
    for sample in data_list:
        try:
            vals = json.loads(sample['value'])
            temperature = max(-50, min(100, float(vals['temperature'])))
            humidity = max(0, min(100, float(vals['humidity'])))
            soil = max(0, min(100, float(vals['soil'])))
            ref.child(sample['created_at'].replace(':', '-').replace('.', '-')).set({
                'created_at': sample['created_at'],
                'temperature': temperature,
                'humidity': humidity,
                'soil': soil
            })
            saved += 1
        except:
            continue
    return saved

def sync_new_data_from_server():
    msgs, latest = ["🔄 Starting sync..."], get_latest_timestamp_from_firebase()
    msgs.append(f"📊 Latest: {latest}" if latest else "📭 No existing data")
    resp = fetch_batch_from_server()
    if "data" not in resp:
        return "\n".join(msgs + ["❌ Error fetching data"]), 0
    new = [s for s in resp["data"] if not latest or s["created_at"] > latest]
    if new:
        saved = save_to_firebase(new)
        return "\n".join(msgs + [f"✨ Found {len(new)} new", f"✅ Saved {saved}!"]), saved
    return "\n".join(msgs + ["✓ No new data"]), 0

def load_data_from_firebase():
    data = db.reference('/sensor_data').get()
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame([{
        'timestamp': pd.to_datetime(v['created_at']),
        'temperature': float(v['temperature']),
        'humidity': float(v['humidity']),
        'soil': float(v['soil'])
    } for v in data.values()])
    df = df.sort_values('timestamp').reset_index(drop=True)
    df['humidity'] = df['humidity'].clip(0, 100)
    df['soil'] = df['soil'].clip(0, 100)
    df['temperature'] = df['temperature'].clip(-50, 100)
    return df

# ============================================================================
# ALERT SYSTEM
# ============================================================================
class AlertSystem:
    """Real-time alert system for disease risks."""
    
    def __init__(self):
        self.alerts = []
        self.alert_ref = db.reference('/alerts')
        self.thresholds = {
            'soil_high': 85, 'soil_low': 25,
            'humidity_high': 80,
            'temperature_high': 35, 'temperature_low': 5,
            'risk_score_critical': 60, 'risk_score_high': 40
        }
    
    def check_conditions(self, temp: float, humidity: float, soil: float, risk_score: int) -> List[Dict]:
        """Check conditions and generate alerts."""
        new_alerts = []
        timestamp = datetime.now().isoformat()
        
        if soil > self.thresholds['soil_high']:
            new_alerts.append({
                'level': 'CRITICAL', 'type': 'WATERLOGGED',
                'message': f'⚠️ CRITICAL: Soil {soil:.1f}% - ROOT ROT RISK!',
                'value': soil, 'threshold': self.thresholds['soil_high'],
                'action': 'Improve drainage immediately',
                'timestamp': timestamp
            })
        elif soil < self.thresholds['soil_low']:
            new_alerts.append({
                'level': 'WARNING', 'type': 'DRY_SOIL',
                'message': f'⚠️ WARNING: Soil {soil:.1f}% - WATER STRESS!',
                'value': soil, 'threshold': self.thresholds['soil_low'],
                'action': 'Irrigate plants',
                'timestamp': timestamp
            })
        
        if humidity > self.thresholds['humidity_high']:
            new_alerts.append({
                'level': 'WARNING', 'type': 'HIGH_HUMIDITY',
                'message': f'⚠️ WARNING: Humidity {humidity:.1f}% - FUNGAL RISK!',
                'value': humidity, 'threshold': self.thresholds['humidity_high'],
                'action': 'Increase ventilation',
                'timestamp': timestamp
            })
        
        if temp > self.thresholds['temperature_high']:
            new_alerts.append({
                'level': 'WARNING', 'type': 'HEAT_STRESS',
                'message': f'⚠️ WARNING: Temp {temp:.1f}°C - HEAT STRESS!',
                'value': temp, 'threshold': self.thresholds['temperature_high'],
                'action': 'Provide shade',
                'timestamp': timestamp
            })
        elif temp < self.thresholds['temperature_low']:
            new_alerts.append({
                'level': 'WARNING', 'type': 'COLD_STRESS',
                'message': f'⚠️ WARNING: Temp {temp:.1f}°C - COLD STRESS!',
                'value': temp, 'threshold': self.thresholds['temperature_low'],
                'action': 'Protect plants',
                'timestamp': timestamp
            })
        
        if risk_score >= self.thresholds['risk_score_critical']:
            new_alerts.append({
                'level': 'CRITICAL', 'type': 'HIGH_DISEASE_RISK',
                'message': f'🔴 CRITICAL: Risk {risk_score}/100 - ACTION REQUIRED!',
                'value': risk_score, 'threshold': self.thresholds['risk_score_critical'],
                'action': 'Inspect plants immediately',
                'timestamp': timestamp
            })
        elif risk_score >= self.thresholds['risk_score_high']:
            new_alerts.append({
                'level': 'WARNING', 'type': 'MODERATE_DISEASE_RISK',
                'message': f'🟡 WARNING: Risk {risk_score}/100 - MONITOR!',
                'value': risk_score, 'threshold': self.thresholds['risk_score_high'],
                'action': 'Increase monitoring',
                'timestamp': timestamp
            })
        
        for alert in new_alerts:
            self.save_alert(alert)
        
        self.alerts.extend(new_alerts)
        return new_alerts
    
    def save_alert(self, alert: Dict):
        """Save alert to Firebase."""
        try:
            timestamp = alert['timestamp'].replace(':', '-').replace('.', '-')
            self.alert_ref.child(timestamp).set(alert)
        except Exception as e:
            print(f"Error saving alert: {e}")
    
    def get_recent_alerts(self, hours: int = 24) -> List[Dict]:
        """Get alerts from last N hours."""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [a for a in self.alerts if datetime.fromisoformat(a['timestamp']) > cutoff]
        return recent
    
    def format_alerts(self, alerts: List[Dict]) -> str:
        """Format alerts for display."""
        if not alerts:
            return "✅ No alerts - All conditions normal"
        
        formatted = ["### 🔔 ACTIVE ALERTS\n"]
        critical = [a for a in alerts if a['level'] == 'CRITICAL']
        warnings = [a for a in alerts if a['level'] == 'WARNING']
        
        if critical:
            formatted.append(f"**🔴 CRITICAL ({len(critical)}):**\n")
            for alert in critical:
                formatted.append(f"- {alert['message']}")
                formatted.append(f"  → Action: {alert['action']}\n")
        
        if warnings:
            formatted.append(f"**🟡 WARNINGS ({len(warnings)}):**\n")
            for alert in warnings:
                formatted.append(f"- {alert['message']}")
                formatted.append(f"  → Action: {alert['action']}\n")
        
        return "\n".join(formatted)

# ============================================================================
# DISEASE PROBABILITY MODEL
# ============================================================================
class DiseaseProbabilityModel:
    """ML-based disease probability prediction."""
    
    def __init__(self):
        self.diseases = {
            'fungal': {
                'name': 'Fungal Diseases',
                'conditions': {'humidity_min': 70, 'temp_min': 20, 'temp_max': 30}
            },
            'bacterial': {
                'name': 'Bacterial Diseases',
                'conditions': {'humidity_min': 85, 'temp_min': 25, 'temp_max': 35}
            },
            'root_rot': {
                'name': 'Root Rot',
                'conditions': {'soil_min': 80, 'humidity_min': 80}
            },
            'heat_stress': {
                'name': 'Heat Stress',
                'conditions': {'temp_min': 35}
            }
        }
    
    def calculate_probability(self, disease_key: str, temp: float, humidity: float, soil: float) -> float:
        """Calculate probability for a specific disease."""
        cond = self.diseases[disease_key]['conditions']
        score = 0
        
        if 'humidity_min' in cond and humidity >= cond['humidity_min']:
            score += 30
        if 'temp_min' in cond and 'temp_max' in cond:
            if cond['temp_min'] <= temp <= cond['temp_max']:
                score += 40
        elif 'temp_min' in cond and temp >= cond['temp_min']:
            score += 40
        if 'soil_min' in cond and soil >= cond['soil_min']:
            score += 30
        
        return min(100, score)
    
    def calculate_all_probabilities(self, temp: float, humidity: float, soil: float) -> Dict:
        """Calculate probabilities for all diseases."""
        probs = {}
        for key, disease in self.diseases.items():
            prob = self.calculate_probability(key, temp, humidity, soil)
            probs[key] = {
                'name': disease['name'],
                'probability': prob
            }
        
        sorted_probs = sorted(probs.items(), key=lambda x: x[1]['probability'], reverse=True)
        return {
            'all': probs,
            'top_risk': {
                'disease': sorted_probs[0][1]['name'],
                'probability': sorted_probs[0][1]['probability']
            }
        }

# ============================================================================
# HISTORICAL ANALYZER
# ============================================================================
class HistoricalAnalyzer:
    """Analyze historical patterns in sensor data."""
    
    def __init__(self):
        self.patterns = []
    
    def analyze_trends(self, df: pd.DataFrame) -> List[Dict]:
        """Analyze data for patterns and trends."""
        if len(df) < 10:
            return []
        
        patterns = []
        
        for col in ['temperature', 'humidity', 'soil']:
            recent = df[col].tail(24)
            older = df[col].head(len(df) - 24) if len(df) > 48 else df[col].head(24)
            
            recent_mean = recent.mean()
            older_mean = older.mean()
            change = recent_mean - older_mean
            
            if abs(change) > 5:
                direction = "increasing" if change > 0 else "decreasing"
                patterns.append({
                    'type': f'{col}_trend',
                    'message': f'{col.capitalize()} is {direction} (Δ{abs(change):.1f})',
                    'severity': 'high' if abs(change) > 10 else 'medium',
                    'value': change
                })
        
        return patterns

# ============================================================================
# PLANT DISEASE IMAGE CLASSIFIER
# ============================================================================
class PlantDiseaseImageClassifier:
    """Image recognition for plant disease detection."""
    
    def __init__(self):
        self.available = False
        if HF_AVAILABLE:
            try:
                self.classifier = pipeline("image-classification", 
                                          model="linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification")
                self.available = True
                print("✓ Image classifier loaded")
            except Exception as e:
                print(f"⚠️ Image classifier unavailable: {e}")
    
    def analyze_image(self, image: Image.Image) -> str:
        """Analyze plant image for diseases."""
        if not self.available:
            return "⚠️ Image classification not available"
        
        try:
            results = self.classifier(image, top_k=3)
            output = "### 🖼️ Image Analysis Results\n\n"
            for i, result in enumerate(results, 1):
                label = result['label'].replace('_', ' ').title()
                score = result['score'] * 100
                output += f"{i}. **{label}**: {score:.1f}%\n"
            return output
        except Exception as e:
            return f"Error analyzing image: {e}"

# ============================================================================
# RAG SYSTEM
# ============================================================================
class PlantDiseaseIndexer:
    """Index plant disease documents for RAG."""
    
    def __init__(self):
        self.chunks = []
        self.stemmer = PorterStemmer()
        self.inverted_index = defaultdict(list)
    
    def preprocess_text(self, text: str) -> str:
        """Clean and normalize text."""
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        return re.sub(r'\s+', ' ', text).strip()
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
        """Split text into overlapping chunks."""
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
        return chunks
    
    def add_document(self, file_path: str):
        """Add PDF document to index."""
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                full_text = ' '.join([page.extract_text() for page in reader.pages])
            
            processed = self.preprocess_text(full_text)
            chunks = self.chunk_text(processed)
            
            for chunk in chunks:
                chunk_id = len(self.chunks)
                self.chunks.append(chunk)
                tokens = word_tokenize(chunk)
                stems = set(self.stemmer.stem(t) for t in tokens)
                for stem in stems:
                    self.inverted_index[stem].append(chunk_id)
            
            print(f"✓ Indexed: {file_path} ({len(chunks)} chunks)")
        except Exception as e:
            print(f"⚠️ Error indexing {file_path}: {e}")
    
    def search(self, query: str, top_k: int = 3) -> List[str]:
        """Search for relevant chunks."""
        query_processed = self.preprocess_text(query)
        tokens = word_tokenize(query_processed)
        stems = [self.stemmer.stem(t) for t in tokens]
        
        scores = defaultdict(float)
        for stem in stems:
            for chunk_id in self.inverted_index.get(stem, []):
                scores[chunk_id] += 1
        
        top_chunks = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [self.chunks[chunk_id] for chunk_id, _ in top_chunks]

class PlantDiseaseRAG:
    """RAG system for plant disease queries."""
    
    def __init__(self, indexer: PlantDiseaseIndexer, client: Cerebras):
        self.indexer = indexer
        self.client = client
    
    def query(self, question: str, n_results: int = 3, temperature: float = 0.3,
              iot_context: str = "", weather_context: str = "") -> str:
        """Answer question using RAG."""
        relevant_chunks = self.indexer.search(question, top_k=n_results)
        
        if not relevant_chunks:
            return "No relevant information found in documents."
        
        context = "\n\n".join([f"[Source {i+1}]:\n{chunk}" 
                               for i, chunk in enumerate(relevant_chunks)])
        
        if iot_context:
            context = f"**CURRENT IoT SENSOR DATA:**\n{iot_context}\n\n{context}"
        if weather_context:
            context = f"**WEATHER FORECAST:**\n{weather_context}\n\n{context}"
        
        prompt = f"""You are an expert agricultural AI assistant. Use the provided context to answer questions about plant diseases, management, and environmental conditions.

CONTEXT:
{context}

QUESTION: {question}

Provide a clear, practical answer based on the context. Include specific recommendations when relevant."""
        
        try:
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=MODEL_NAME,
                temperature=temperature,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating response: {e}"

# ============================================================================
# UI COMPONENTS
# ============================================================================
CUSTOM_CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
* {{ font-family: 'Inter', sans-serif; }}
.kpi-card {{ background: white; padding: 24px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.12);
  text-align: center; transition: transform 0.2s; border-left: 4px solid; }}
.kpi-card:hover {{ transform: translateY(-4px); box-shadow: 0 3px 6px rgba(0,0,0,0.16); }}
.kpi-label {{ color: #6b7280; font-size: 14px; font-weight: 600; text-transform: uppercase; }}
.kpi-value {{ font-size: 48px; font-weight: 700; margin: 8px 0; color: #1f2937; }}
.kpi-change {{ font-size: 14px; font-weight: 600; }}
.trend-up {{ color: #10b981; }} .trend-down {{ color: #ef4444; }} .trend-stable {{ color: #3b82f6; }}
.stat-card {{ border-radius: 16px; padding: 24px; color: white; box-shadow: 0 3px 6px rgba(0,0,0,0.16); margin: 16px 0; }}
.stat-item {{ background: rgba(255,255,255,0.2); border-radius: 12px; padding: 16px; }}
.status-badge {{ display: inline-flex; align-items: center; gap: 6px; padding: 6px 16px; border-radius: 20px;
  font-size: 14px; font-weight: 600; background: #dcfce7; color: #166534; }}
.status-dot {{ width: 8px; height: 8px; border-radius: 50%; background: #10b981; animation: pulse 2s infinite; }}
@keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.5; }} }}
"""

def create_kpi_card(label, value, unit, change, change_label, trend="up", border_color=None):
    bc = border_color or COLORS['status']['normal']
    icon = "↑" if trend == "up" else ("↓" if trend == "down" else "→")
    return f'''<div class="kpi-card" style="border-left-color: {bc};">
        <p class="kpi-label">{label}</p>
        <p class="kpi-value">{value}<span style="font-size: 24px;">{unit}</span></p>
        <p class="kpi-change trend-{trend}"><span>{icon}</span> {change} {change_label}</p>
    </div>'''

def create_status_badge(text="LIVE", pulse=True):
    return f'<span class="status-badge">{"<span class=\"status-dot\"></span>" if pulse else ""}{text}</span>'

def create_stat_cards_html(df):
    if len(df) == 0:
        return "<p>No data available</p>"
    
    html = '<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px;">'
    for var, unit, _, grad, name in SENSORS:
        stats_dict = {
            'Mean': df[var].mean(),
            'Median': df[var].median(),
            'Std Dev': df[var].std(),
            'Min': df[var].min(),
            'Max': df[var].max()
        }
        
        html += f'<div class="stat-card" style="background: {grad};"><h2>{name}</h2>'
        html += '<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px;">'
        for stat_name, stat_val in stats_dict.items():
            html += f'''<div class="stat-item">
                <div style="font-size: 13px; font-weight: 500;">{stat_name}</div>
                <div style="font-size: 26px; font-weight: 700;">{stat_val:.2f}{unit}</div>
            </div>'''
        html += '</div></div>'
    html += '</div>'
    return html

# ============================================================================
# PLOT FUNCTIONS
# ============================================================================
def apply_chart_styling(fig, title="", xaxis_title="", yaxis_title="", height=400):
    fig.update_layout(
        title=dict(text=title, font=dict(size=20)),
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        font=dict(family="Inter, sans-serif", size=14),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=height,
        hovermode='x unified'
    )
    fig.update_xaxes(showgrid=False, title_font=dict(size=14, color='#6b7280'))
    fig.update_yaxes(showgrid=True, gridcolor='#E5E7EB', title_font=dict(size=14, color='#6b7280'))
    return fig

def time_series_overview(df):
    fig = go.Figure()
    for col, unit, color, _, _ in SENSORS:
        fig.add_trace(go.Scatter(
            x=df['timestamp'], y=df[col], name=col.capitalize(),
            mode='lines', line=dict(color=color, width=2),
            hovertemplate=f'%{{y:.1f}}{unit}<extra></extra>'
        ))
    apply_chart_styling(fig, "Sensor Data Time Series", "Time", "Measurement", 500)
    return fig

def calculate_correlations(df):
    corr = df[['temperature', 'humidity', 'soil']].corr()
    fig = px.imshow(
        corr,
        labels=dict(color="Correlation"),
        x=['Temperature', 'Humidity', 'Soil'],
        y=['Temperature', 'Humidity', 'Soil'],
        color_continuous_scale='RdBu_r',
        zmin=-1, zmax=1
    )
    fig.update_layout(height=400, title="Correlation Matrix")
    return fig

def anomaly_detection(df):
    df_copy = df.copy()
    anomalies = pd.DataFrame()
    for col in ['temperature', 'humidity', 'soil']:
        z = np.abs(stats.zscore(df_copy[col]))
        anom = df_copy[z > 3].copy()
        if len(anom) > 0:
            anom['variable'] = col
            anom['z_score'] = z[z > 3]
            anomalies = pd.concat([anomalies, anom[['timestamp', 'variable', col, 'z_score']]])
    
    if len(anomalies) > 0:
        return anomalies.round(3).sort_values('timestamp').reset_index(drop=True)
    else:
        return pd.DataFrame({'Message': ['No anomalies detected']})

# ============================================================================
# MAIN APPLICATION
# ============================================================================
def create_integrated_dashboard():
    """Create integrated dashboard with all features."""
    
    # Initialize components
    print("🚀 Initializing system...")
    weather_service = WeatherService()
    alert_system = AlertSystem()
    prob_model = DiseaseProbabilityModel()
    historical_analyzer = HistoricalAnalyzer()
    image_classifier = PlantDiseaseImageClassifier()
    
    # Load initial data
    print('📥 Loading data...')
    sync_msg, synced = sync_new_data_from_server()
    print(sync_msg)
    df = load_data_from_firebase()
    print(f'✓ Loaded {len(df)} records')
    
    # Initialize RAG
    indexer = PlantDiseaseIndexer()
    # Add documents if available
    doc_files = ['plant_diseases.pdf', 'agriculture_guide.pdf']
    for doc in doc_files:
        if os.path.exists(doc):
            indexer.add_document(doc)
    rag = PlantDiseaseRAG(indexer, client)
    
    print("✅ System ready!")
    
    # Create Gradio interface
    with gr.Blocks(css=CUSTOM_CSS, theme=gr.themes.Soft(), title="Integrated Plant System") as demo:
        gr.Markdown("""
        # 🌱 Integrated Smart Plant Disease Detection & Sensor Analytics
        ## IoT Monitoring + Disease Detection + Weather + ML + AI Assistant
        """)
        
        with gr.Row():
            gr.HTML(create_status_badge("LIVE", pulse=True))
            data_info = gr.Markdown(
                f"**📊 Data:** {len(df)} records" +
                (f" | **📅 Range:** {df['timestamp'].min()} to {df['timestamp'].max()}" if len(df) > 0 else "")
            )
        
        with gr.Row():
            sync_btn = gr.Button("🔄 Sync & Refresh", variant="primary", size="lg")
        sync_status = gr.Textbox(label="📡 Sync Status", lines=4, interactive=False)
        
        gr.Markdown("## 📈 Key Performance Indicators")
        with gr.Row(equal_height=True):
            if len(df) > 0:
                kpi_data = [(df[col].iloc[-1], df[col].mean(), col, unit, color)
                           for col, unit, color, _, _ in SENSORS]
            else:
                kpi_data = [(0, 0, col, unit, color) for col, unit, color, _, _ in SENSORS]
            
            kpi_outputs = []
            for current, mean, col, unit, color in kpi_data:
                change = current - mean
                kpi_outputs.append(gr.HTML(create_kpi_card(
                    col.capitalize(), f"{current:.1f}", unit,
                    f"{abs(change):.1f}{unit}", "vs avg",
                    "up" if change > 0 else "down", color
                )))
        
        with gr.Tab("📊 Statistics & Analytics"):
            basic_cards = gr.HTML(create_stat_cards_html(df))
            gr.Markdown("### Time Series")
            ts_plot = gr.Plot()
            gr.Markdown("### Correlations")
            corr_plot = gr.Plot()
            gr.Markdown("### Anomalies")
            anomaly_table = gr.Dataframe(label="Detected Anomalies", wrap=True)
        
        with gr.Tab("🔔 Alerts & Disease Risk"):
            alerts_display = gr.Markdown("### Current Alerts")
            disease_risk_display = gr.Markdown("### Disease Probabilities")
            weather_display = gr.Markdown("### Weather Forecast")
            
            refresh_alerts_btn = gr.Button("🔄 Refresh Alerts")
        
        with gr.Tab("💬 AI Assistant"):
            gr.Markdown("### Ask questions about plant diseases and agriculture")
            with gr.Row():
                question = gr.Textbox(
                    label="Question",
                    lines=3,
                    placeholder="e.g., What are common fig diseases?"
                )
                n_results = gr.Slider(1, 5, 3, step=1, label="Sources")
            
            submit_btn = gr.Button("🚀 Ask AI", variant="primary", size="lg")
            answer = gr.Markdown()
        
        with gr.Tab("🖼️ Image Analysis"):
            gr.Markdown("### Upload a leaf photo for disease detection")
            image_input = gr.Image(type="pil", label="Upload Leaf Photo")
            analyze_btn = gr.Button("🔍 Analyze Image", variant="primary")
            image_result = gr.Markdown()
        
        # Event handlers
        def sync_and_refresh():
            nonlocal df
            status, _ = sync_new_data_from_server()
            df = load_data_from_firebase()
            
            if len(df) > 0:
                info = f"**📊 Data:** {len(df)} records | **📅 Range:** {df['timestamp'].min()} to {df['timestamp'].max()}"
                kpi_updates = []
                for col, unit, color, _, _ in SENSORS:
                    current, mean = df[col].iloc[-1], df[col].mean()
                    change = current - mean
                    kpi_updates.append(create_kpi_card(
                        col.capitalize(), f"{current:.1f}", unit,
                        f"{abs(change):.1f}{unit}", "vs avg",
                        "up" if change > 0 else "down", color
                    ))
                
                return [status, info] + kpi_updates + [
                    create_stat_cards_html(df),
                    time_series_overview(df),
                    calculate_correlations(df),
                    anomaly_detection(df)
                ]
            return [status, "**No data**"] + [""] * (len(kpi_outputs) + 4)
        
        def refresh_alerts_and_risks():
            if len(df) == 0:
                return "No data available", "No data available", "No data available"
            
            latest = df.iloc[-1]
            
            # Calculate disease probabilities
            probs = prob_model.calculate_all_probabilities(
                latest['temperature'], latest['humidity'], latest['soil']
            )
            
            # Check for alerts
            risk_score = probs['top_risk']['probability']
            alerts = alert_system.check_conditions(
                latest['temperature'], latest['humidity'], latest['soil'], int(risk_score)
            )
            
            # Format outputs
            alerts_text = alert_system.format_alerts(alerts)
            
            disease_text = f"### 📊 Disease Risk Assessment\n\n"
            disease_text += f"**Top Risk:** {probs['top_risk']['disease']} ({probs['top_risk']['probability']:.0f}%)\n\n"
            for key, data in probs['all'].items():
                disease_text += f"- **{data['name']}**: {data['probability']:.0f}%\n"
            
            # Get weather forecast
            forecast = weather_service.get_forecast(7)
            if not forecast.empty:
                weather_risk = weather_service.predict_disease_risk_from_forecast(forecast)
                weather_text = f"### 🌤️ 7-Day Weather Forecast\n\n"
                weather_text += f"**Disease Risk Level:** {weather_risk['risk_level']}\n"
                weather_text += f"**Risk Score:** {weather_risk['risk_score']}/100\n\n"
                if weather_risk['risk_factors']:
                    weather_text += "**Risk Factors:**\n"
                    for factor in weather_risk['risk_factors']:
                        weather_text += f"- {factor}\n"
            else:
                weather_text = "Weather data unavailable"
            
            return alerts_text, disease_text, weather_text
        
        def ask_ai(question, n_results):
            if len(df) == 0:
                return rag.query(question, n_results)
            
            latest = df.iloc[-1]
            iot_context = f"Temperature: {latest['temperature']:.1f}°C, Humidity: {latest['humidity']:.1f}%, Soil: {latest['soil']:.1f}%"
            return rag.query(question, n_results, iot_context=iot_context)
        
        def analyze_image_handler(image):
            return image_classifier.analyze_image(image)
        
        # Connect buttons
        sync_btn.click(
            sync_and_refresh,
            outputs=[sync_status, data_info] + kpi_outputs + [
                basic_cards, ts_plot, corr_plot, anomaly_table
            ]
        )
        
        refresh_alerts_btn.click(
            refresh_alerts_and_risks,
            outputs=[alerts_display, disease_risk_display, weather_display]
        )
        
        submit_btn.click(
            ask_ai,
            inputs=[question, n_results],
            outputs=answer
        )
        
        analyze_btn.click(
            analyze_image_handler,
            inputs=image_input,
            outputs=image_result
        )
        
        # Load initial data
        if len(df) > 0:
            demo.load(
                lambda: [
                    create_stat_cards_html(df),
                    time_series_overview(df),
                    calculate_correlations(df),
                    anomaly_detection(df)
                ] + list(refresh_alerts_and_risks()),
                outputs=[basic_cards, ts_plot, corr_plot, anomaly_table,
                        alerts_display, disease_risk_display, weather_display]
            )
    
    return demo

# ============================================================================
# ENTRY POINT
# ============================================================================
if __name__ == "__main__":
    print("=" * 80)
    print("🌱 INTEGRATED SMART PLANT DISEASE DETECTION & SENSOR ANALYTICS SYSTEM")
    print("=" * 80)
    
    demo = create_integrated_dashboard()
    demo.launch(share=True, debug=True)
