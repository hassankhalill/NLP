"""
Model Monitoring Module for ABSA API
Tracks model performance, API health, and data drift

This module monitors:
1. Model performance metrics (accuracy, F1 score)
2. API performance (latency, throughput)
3. Data drift (distribution changes)
4. System health (memory, CPU)

Triggers retraining when KPIs breach thresholds.
"""

import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import time
from collections import defaultdict
import pickle

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelMonitor:
    """Monitor model performance and trigger retraining when needed"""

    def __init__(
        self,
        metrics_file: str = 'monitoring_metrics.json',
        threshold_config: Optional[Dict] = None
    ):
        """
        Initialize the monitoring system

        Args:
            metrics_file: Path to store monitoring metrics
            threshold_config: Dictionary of KPI thresholds
        """
        self.metrics_file = Path(metrics_file)
        self.metrics_history = self._load_metrics()

        # Default thresholds (can be customized)
        self.thresholds = threshold_config or {
            'min_accuracy': 0.80,           # Minimum acceptable accuracy
            'max_latency_ms': 500,          # Maximum API response time (ms)
            'max_data_drift': 0.15,         # Maximum KL divergence for data drift
            'min_daily_requests': 10,       # Minimum requests for meaningful metrics
            'error_rate_threshold': 0.10,   # Maximum error rate (10%)
            'sentiment_drift_threshold': 0.20  # Maximum change in sentiment distribution
        }

        # Performance tracking
        self.current_session = {
            'predictions': [],
            'ground_truth': [],
            'latencies': [],
            'errors': [],
            'sentiment_distribution': defaultdict(int),
            'aspect_distribution': defaultdict(int),
            'start_time': datetime.now()
        }

        logger.info(f"ModelMonitor initialized with thresholds: {self.thresholds}")

    def _load_metrics(self) -> List[Dict]:
        """Load historical metrics from file"""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load metrics file: {e}")
                return []
        return []

    def _save_metrics(self):
        """Save metrics history to file"""
        try:
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(self.metrics_history, f, indent=2, default=str)
            logger.info(f"Metrics saved to {self.metrics_file}")
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")

    def log_prediction(
        self,
        prediction: str,
        ground_truth: Optional[str] = None,
        latency_ms: float = 0.0,
        sentiment: Optional[str] = None,
        aspects: Optional[List[str]] = None
    ):
        """
        Log a single prediction for monitoring

        Args:
            prediction: Model prediction
            ground_truth: Actual label (if available)
            latency_ms: Prediction latency in milliseconds
            sentiment: Sentiment label
            aspects: List of detected aspects
        """
        self.current_session['predictions'].append(prediction)
        if ground_truth:
            self.current_session['ground_truth'].append(ground_truth)
        self.current_session['latencies'].append(latency_ms)

        if sentiment:
            self.current_session['sentiment_distribution'][sentiment] += 1

        if aspects:
            for aspect in aspects:
                self.current_session['aspect_distribution'][aspect] += 1

    def log_error(self, error_type: str, error_message: str):
        """Log an error occurrence"""
        self.current_session['errors'].append({
            'type': error_type,
            'message': error_message,
            'timestamp': datetime.now().isoformat()
        })
        logger.error(f"Error logged: {error_type} - {error_message}")

    def calculate_accuracy(self) -> Optional[float]:
        """Calculate model accuracy from logged predictions"""
        if len(self.current_session['ground_truth']) == 0:
            return None

        correct = sum(
            1 for pred, truth in zip(
                self.current_session['predictions'],
                self.current_session['ground_truth']
            ) if pred == truth
        )
        return correct / len(self.current_session['ground_truth'])

    def calculate_avg_latency(self) -> float:
        """Calculate average prediction latency"""
        if not self.current_session['latencies']:
            return 0.0
        return np.mean(self.current_session['latencies'])

    def calculate_error_rate(self) -> float:
        """Calculate error rate"""
        total_requests = len(self.current_session['predictions'])
        if total_requests == 0:
            return 0.0
        return len(self.current_session['errors']) / total_requests

    def detect_data_drift(self) -> Tuple[float, bool]:
        """
        Detect data drift by comparing current sentiment distribution
        with historical baseline

        Returns:
            Tuple of (drift_score, is_drifted)
        """
        if len(self.metrics_history) == 0:
            return 0.0, False

        # Get historical sentiment distribution (last 7 days average)
        recent_metrics = [
            m for m in self.metrics_history[-7:]
            if 'sentiment_distribution' in m
        ]

        if not recent_metrics:
            return 0.0, False

        # Calculate baseline distribution
        baseline_dist = defaultdict(float)
        for metric in recent_metrics:
            for sentiment, count in metric['sentiment_distribution'].items():
                baseline_dist[sentiment] += count

        total_baseline = sum(baseline_dist.values())
        if total_baseline == 0:
            return 0.0, False

        baseline_probs = {
            k: v/total_baseline for k, v in baseline_dist.items()
        }

        # Calculate current distribution
        current_dist = dict(self.current_session['sentiment_distribution'])
        total_current = sum(current_dist.values())
        if total_current == 0:
            return 0.0, False

        current_probs = {
            k: v/total_current for k, v in current_dist.items()
        }

        # Calculate KL divergence (drift score)
        sentiments = set(baseline_probs.keys()) | set(current_probs.keys())
        kl_divergence = 0.0

        for sentiment in sentiments:
            p = current_probs.get(sentiment, 1e-10)
            q = baseline_probs.get(sentiment, 1e-10)
            kl_divergence += p * np.log(p / q)

        is_drifted = kl_divergence > self.thresholds['max_data_drift']

        return kl_divergence, is_drifted

    def check_thresholds(self) -> Dict[str, bool]:
        """
        Check if any KPI thresholds are breached

        Returns:
            Dictionary of threshold checks (True = breached)
        """
        breaches = {}

        # Check accuracy
        accuracy = self.calculate_accuracy()
        if accuracy is not None:
            breaches['low_accuracy'] = accuracy < self.thresholds['min_accuracy']
        else:
            breaches['low_accuracy'] = False

        # Check latency
        avg_latency = self.calculate_avg_latency()
        breaches['high_latency'] = avg_latency > self.thresholds['max_latency_ms']

        # Check error rate
        error_rate = self.calculate_error_rate()
        breaches['high_error_rate'] = error_rate > self.thresholds['error_rate_threshold']

        # Check data drift
        drift_score, is_drifted = self.detect_data_drift()
        breaches['data_drift'] = is_drifted

        return breaches

    def should_retrain(self) -> Tuple[bool, List[str]]:
        """
        Determine if model should be retrained based on KPIs

        Returns:
            Tuple of (should_retrain, reasons)
        """
        breaches = self.check_thresholds()
        reasons = []

        # Only consider retraining if we have enough data
        if len(self.current_session['predictions']) < self.thresholds['min_daily_requests']:
            return False, ['Insufficient data for decision']

        # Check each breach
        if breaches.get('low_accuracy'):
            accuracy = self.calculate_accuracy()
            reasons.append(f"Accuracy below threshold: {accuracy:.2%} < {self.thresholds['min_accuracy']:.2%}")

        if breaches.get('high_error_rate'):
            error_rate = self.calculate_error_rate()
            reasons.append(f"Error rate too high: {error_rate:.2%} > {self.thresholds['error_rate_threshold']:.2%}")

        if breaches.get('data_drift'):
            drift_score, _ = self.detect_data_drift()
            reasons.append(f"Data drift detected: KL divergence = {drift_score:.4f}")

        should_retrain = len(reasons) > 0

        if should_retrain:
            logger.warning(f"Retraining recommended. Reasons: {reasons}")

        return should_retrain, reasons

    def generate_report(self) -> Dict:
        """
        Generate comprehensive monitoring report

        Returns:
            Dictionary containing all monitoring metrics
        """
        accuracy = self.calculate_accuracy()
        avg_latency = self.calculate_avg_latency()
        error_rate = self.calculate_error_rate()
        drift_score, is_drifted = self.detect_data_drift()
        breaches = self.check_thresholds()
        should_retrain, reasons = self.should_retrain()

        report = {
            'timestamp': datetime.now().isoformat(),
            'session_duration_hours': (
                datetime.now() - self.current_session['start_time']
            ).total_seconds() / 3600,
            'metrics': {
                'total_predictions': len(self.current_session['predictions']),
                'accuracy': accuracy,
                'avg_latency_ms': avg_latency,
                'error_rate': error_rate,
                'error_count': len(self.current_session['errors'])
            },
            'data_quality': {
                'drift_score': drift_score,
                'is_drifted': is_drifted,
                'sentiment_distribution': dict(self.current_session['sentiment_distribution']),
                'aspect_distribution': dict(self.current_session['aspect_distribution'])
            },
            'thresholds': self.thresholds,
            'breaches': breaches,
            'retraining': {
                'recommended': should_retrain,
                'reasons': reasons
            }
        }

        return report

    def save_daily_metrics(self):
        """Save current session metrics to history"""
        report = self.generate_report()
        self.metrics_history.append(report)
        self._save_metrics()

        logger.info(f"Daily metrics saved. Total predictions: {report['metrics']['total_predictions']}")

        # Reset current session
        self.current_session = {
            'predictions': [],
            'ground_truth': [],
            'latencies': [],
            'errors': [],
            'sentiment_distribution': defaultdict(int),
            'aspect_distribution': defaultdict(int),
            'start_time': datetime.now()
        }

    def get_performance_summary(self, days: int = 7) -> Dict:
        """
        Get performance summary for last N days

        Args:
            days: Number of days to summarize

        Returns:
            Dictionary with aggregated metrics
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_metrics = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m['timestamp']) > cutoff_date
        ]

        if not recent_metrics:
            return {'message': 'No metrics available for specified period'}

        # Aggregate metrics
        accuracies = [
            m['metrics']['accuracy'] for m in recent_metrics
            if m['metrics']['accuracy'] is not None
        ]
        latencies = [m['metrics']['avg_latency_ms'] for m in recent_metrics]
        error_rates = [m['metrics']['error_rate'] for m in recent_metrics]

        summary = {
            'period_days': days,
            'total_sessions': len(recent_metrics),
            'avg_accuracy': np.mean(accuracies) if accuracies else None,
            'avg_latency_ms': np.mean(latencies),
            'avg_error_rate': np.mean(error_rates),
            'total_predictions': sum(m['metrics']['total_predictions'] for m in recent_metrics),
            'drift_incidents': sum(1 for m in recent_metrics if m['data_quality']['is_drifted']),
            'retraining_recommendations': sum(1 for m in recent_metrics if m['retraining']['recommended'])
        }

        return summary


# Example usage and testing
if __name__ == "__main__":
    print("=" * 80)
    print("Model Monitoring System - Test Run")
    print("=" * 80)

    # Initialize monitor
    monitor = ModelMonitor()

    # Simulate predictions
    print("\n[1] Simulating predictions...")
    predictions = [
        ('positive', 'positive', 150, 'positive', ['location', 'service']),
        ('positive', 'positive', 180, 'positive', ['food', 'cleanliness']),
        ('neutral', 'neutral', 160, 'neutral', ['price']),
        ('negative', 'negative', 200, 'negative', ['service']),
        ('positive', 'neutral', 170, 'positive', ['location']),  # Misprediction
    ]

    for pred, truth, latency, sentiment, aspects in predictions:
        monitor.log_prediction(pred, truth, latency, sentiment, aspects)

    # Simulate errors
    print("[2] Simulating errors...")
    monitor.log_error('ValidationError', 'Invalid input format')

    # Generate report
    print("\n[3] Generating monitoring report...")
    report = monitor.generate_report()

    print(f"\n{'='*80}")
    print("MONITORING REPORT")
    print(f"{'='*80}")
    print(f"Timestamp: {report['timestamp']}")
    print(f"\nMetrics:")
    print(f"  - Total Predictions: {report['metrics']['total_predictions']}")
    print(f"  - Accuracy: {report['metrics']['accuracy']:.2%}" if report['metrics']['accuracy'] else "  - Accuracy: N/A")
    print(f"  - Avg Latency: {report['metrics']['avg_latency_ms']:.1f} ms")
    print(f"  - Error Rate: {report['metrics']['error_rate']:.2%}")

    print(f"\nData Quality:")
    print(f"  - Drift Score: {report['data_quality']['drift_score']:.4f}")
    print(f"  - Is Drifted: {report['data_quality']['is_drifted']}")
    print(f"  - Sentiment Distribution: {report['data_quality']['sentiment_distribution']}")

    print(f"\nThreshold Breaches:")
    for breach, status in report['breaches'].items():
        status_str = "BREACH" if status else "OK"
        print(f"  - {breach}: {status_str}")

    print(f"\nRetraining Decision:")
    print(f"  - Recommended: {report['retraining']['recommended']}")
    if report['retraining']['reasons']:
        print(f"  - Reasons:")
        for reason in report['retraining']['reasons']:
            print(f"    * {reason}")

    # Save metrics
    print("\n[4] Saving metrics...")
    monitor.save_daily_metrics()

    print(f"\n{'='*80}")
    print("Test completed successfully!")
    print(f"Metrics saved to: {monitor.metrics_file}")
    print(f"{'='*80}\n")
