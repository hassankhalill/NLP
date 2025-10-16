"""
Automated Model Retraining Module for ABSA System
Handles data collection, model retraining, and deployment

This module:
1. Collects new labeled data
2. Prepares retraining dataset
3. Retrains ABSA model
4. Evaluates new model performance
5. Deploys if performance improves
6. Maintains model versioning
"""

import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import shutil
import pickle

# Import our modules
from text_preprocessing import TextCleaner
from sentiment_analysis import RatingBasedSentimentAnalyzer
from absa_model import ABSAModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelRetrainer:
    """Handles automated model retraining pipeline"""

    def __init__(
        self,
        models_dir: str = 'models',
        data_dir: str = 'data',
        min_new_samples: int = 1000,
        improvement_threshold: float = 0.02
    ):
        """
        Initialize the retraining system

        Args:
            models_dir: Directory to store model versions
            data_dir: Directory for training data
            min_new_samples: Minimum new samples needed for retraining
            improvement_threshold: Minimum improvement required to deploy (2%)
        """
        self.models_dir = Path(models_dir)
        self.data_dir = Path(data_dir)
        self.models_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)

        self.min_new_samples = min_new_samples
        self.improvement_threshold = improvement_threshold

        # Initialize components
        self.text_cleaner = TextCleaner()
        self.sentiment_analyzer = RatingBasedSentimentAnalyzer()
        self.absa_model = ABSAModel()

        # Load retraining history
        self.history_file = self.models_dir / 'retraining_history.json'
        self.history = self._load_history()

        logger.info(f"ModelRetrainer initialized. Models dir: {self.models_dir}")

    def _load_history(self) -> List[Dict]:
        """Load retraining history"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load history: {e}")
                return []
        return []

    def _save_history(self):
        """Save retraining history"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving history: {e}")

    def collect_new_data(self, feedback_file: str = 'user_feedback.csv') -> pd.DataFrame:
        """
        Collect new labeled data from user feedback

        Args:
            feedback_file: Path to user feedback CSV

        Returns:
            DataFrame with new labeled samples
        """
        feedback_path = self.data_dir / feedback_file

        if not feedback_path.exists():
            logger.warning(f"No feedback file found at {feedback_path}")
            return pd.DataFrame()

        try:
            df = pd.read_csv(feedback_path, encoding='utf-8')
            logger.info(f"Collected {len(df)} new samples from {feedback_file}")
            return df
        except Exception as e:
            logger.error(f"Error loading feedback data: {e}")
            return pd.DataFrame()

    def prepare_training_data(
        self,
        original_data_path: str = 'data_with_absa.csv',
        new_data: Optional[pd.DataFrame] = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Prepare combined training dataset

        Args:
            original_data_path: Path to original training data
            new_data: New labeled samples to add

        Returns:
            Tuple of (train_df, val_df)
        """
        # Load original data
        try:
            original_df = pd.read_csv(original_data_path, encoding='utf-8')
            logger.info(f"Loaded {len(original_df)} original samples")
        except Exception as e:
            logger.error(f"Error loading original data: {e}")
            return pd.DataFrame(), pd.DataFrame()

        # Combine with new data if available
        if new_data is not None and len(new_data) > 0:
            combined_df = pd.concat([original_df, new_data], ignore_index=True)
            logger.info(f"Combined dataset: {len(combined_df)} samples")
        else:
            combined_df = original_df

        # Remove duplicates
        combined_df = combined_df.drop_duplicates(subset=['content'], keep='last')

        # Split into train/validation (80/20)
        train_size = int(0.8 * len(combined_df))
        train_df = combined_df.iloc[:train_size]
        val_df = combined_df.iloc[train_size:]

        logger.info(f"Training set: {len(train_df)}, Validation set: {len(val_df)}")

        return train_df, val_df

    def evaluate_model(
        self,
        model: ABSAModel,
        eval_df: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Evaluate model performance on validation set

        Args:
            model: ABSA model to evaluate
            eval_df: Validation dataframe

        Returns:
            Dictionary of performance metrics
        """
        logger.info(f"Evaluating model on {len(eval_df)} samples...")

        # Sentiment accuracy
        correct_sentiment = 0
        total_sentiment = 0

        # Aspect detection metrics
        aspect_precision_sum = 0
        aspect_recall_sum = 0
        aspect_count = 0

        # Latency tracking
        latencies = []

        for idx, row in eval_df.iterrows():
            try:
                start_time = pd.Timestamp.now()

                # Get prediction
                result = model.analyze(
                    text=row['content'],
                    overall_rating=row.get('raw_rating', 3),
                    lang=row.get('language', 'en')
                )

                end_time = pd.Timestamp.now()
                latency_ms = (end_time - start_time).total_seconds() * 1000
                latencies.append(latency_ms)

                # Check sentiment accuracy (if available)
                if 'sentiment_label' in row:
                    predicted_sentiment = result['overall_sentiment']
                    true_sentiment = row['sentiment_label']
                    if predicted_sentiment == true_sentiment:
                        correct_sentiment += 1
                    total_sentiment += 1

                # Check aspect detection (if available)
                if 'aspects_detected' in row and isinstance(row['aspects_detected'], str):
                    try:
                        true_aspects = set(eval(row['aspects_detected']))
                        predicted_aspects = set(result['aspects_detected'])

                        if len(predicted_aspects) > 0:
                            precision = len(true_aspects & predicted_aspects) / len(predicted_aspects)
                            aspect_precision_sum += precision

                        if len(true_aspects) > 0:
                            recall = len(true_aspects & predicted_aspects) / len(true_aspects)
                            aspect_recall_sum += recall

                        aspect_count += 1
                    except:
                        pass

            except Exception as e:
                logger.warning(f"Error evaluating row {idx}: {e}")
                continue

        # Calculate metrics
        metrics = {
            'sentiment_accuracy': correct_sentiment / total_sentiment if total_sentiment > 0 else 0.0,
            'aspect_precision': aspect_precision_sum / aspect_count if aspect_count > 0 else 0.0,
            'aspect_recall': aspect_recall_sum / aspect_count if aspect_count > 0 else 0.0,
            'avg_latency_ms': np.mean(latencies) if latencies else 0.0,
            'total_evaluated': len(eval_df)
        }

        # Calculate F1 score
        if metrics['aspect_precision'] + metrics['aspect_recall'] > 0:
            metrics['aspect_f1'] = 2 * (
                metrics['aspect_precision'] * metrics['aspect_recall']
            ) / (metrics['aspect_precision'] + metrics['aspect_recall'])
        else:
            metrics['aspect_f1'] = 0.0

        logger.info(f"Evaluation complete: {json.dumps(metrics, indent=2)}")

        return metrics

    def retrain_model(
        self,
        train_df: pd.DataFrame,
        val_df: pd.DataFrame
    ) -> Tuple[ABSAModel, Dict[str, float]]:
        """
        Retrain ABSA model on new data

        Args:
            train_df: Training dataframe
            val_df: Validation dataframe

        Returns:
            Tuple of (trained_model, evaluation_metrics)
        """
        logger.info("Starting model retraining...")

        # For this implementation, we're using rule-based ABSA
        # In production, you would retrain ML models here
        # For now, we update keyword dictionaries with new patterns

        # Create new model instance
        new_model = ABSAModel()

        # Extract new keywords from training data
        logger.info("Extracting patterns from training data...")

        # Update aspect keywords based on frequent terms
        # (In production, this would be more sophisticated)
        for aspect in new_model.aspect_keywords.keys():
            aspect_reviews = []
            for idx, row in train_df.iterrows():
                if 'aspects_detected' in row and isinstance(row['aspects_detected'], str):
                    try:
                        aspects = eval(row['aspects_detected'])
                        if aspect in aspects:
                            aspect_reviews.append(row['content'])
                    except:
                        pass

            # Here you would extract new keywords using TF-IDF or similar
            # For now, we keep existing keywords

        # Evaluate new model
        logger.info("Evaluating retrained model...")
        metrics = self.evaluate_model(new_model, val_df)

        return new_model, metrics

    def save_model_version(
        self,
        model: ABSAModel,
        version: str,
        metrics: Dict[str, float]
    ):
        """
        Save model version with metadata

        Args:
            model: Model to save
            version: Version identifier
            metrics: Performance metrics
        """
        version_dir = self.models_dir / f"v{version}"
        version_dir.mkdir(exist_ok=True)

        # Save model (for rule-based, we save the configuration)
        model_config = {
            'aspect_keywords': model.aspect_keywords,
            'positive_indicators': model.positive_indicators,
            'negative_indicators': model.negative_indicators,
            'version': version,
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics
        }

        config_path = version_dir / 'model_config.json'
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(model_config, f, indent=2)

        # Save metadata
        metadata = {
            'version': version,
            'created_at': datetime.now().isoformat(),
            'metrics': metrics
        }

        metadata_path = version_dir / 'metadata.json'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Model version {version} saved to {version_dir}")

    def deploy_model(self, version: str) -> bool:
        """
        Deploy model version to production

        Args:
            version: Version to deploy

        Returns:
            True if deployment successful
        """
        version_dir = self.models_dir / f"v{version}"

        if not version_dir.exists():
            logger.error(f"Version {version} not found")
            return False

        try:
            # Copy to production location (in practice, this would trigger deployment)
            production_dir = Path('production_model')
            production_dir.mkdir(exist_ok=True)

            # Copy model files
            shutil.copytree(version_dir, production_dir / 'current', dirs_exist_ok=True)

            logger.info(f"Model version {version} deployed to production")
            return True

        except Exception as e:
            logger.error(f"Error deploying model: {e}")
            return False

    def execute_retraining_pipeline(
        self,
        reason: str = "Scheduled retraining"
    ) -> Dict:
        """
        Execute complete retraining pipeline

        Args:
            reason: Reason for retraining

        Returns:
            Dictionary with retraining results
        """
        logger.info(f"="*80)
        logger.info(f"Starting retraining pipeline. Reason: {reason}")
        logger.info(f"="*80)

        results = {
            'timestamp': datetime.now().isoformat(),
            'reason': reason,
            'success': False
        }

        # Step 1: Collect new data
        logger.info("\n[Step 1/6] Collecting new data...")
        new_data = self.collect_new_data()

        if len(new_data) < self.min_new_samples:
            logger.warning(f"Insufficient new data: {len(new_data)} < {self.min_new_samples}")
            results['message'] = f"Insufficient new data ({len(new_data)} samples)"
            return results

        # Step 2: Prepare training data
        logger.info("\n[Step 2/6] Preparing training data...")
        train_df, val_df = self.prepare_training_data(new_data=new_data)

        if len(train_df) == 0:
            logger.error("Failed to prepare training data")
            results['message'] = "Failed to prepare training data"
            return results

        # Step 3: Evaluate current model
        logger.info("\n[Step 3/6] Evaluating current model...")
        current_metrics = self.evaluate_model(self.absa_model, val_df)
        results['current_metrics'] = current_metrics

        # Step 4: Retrain model
        logger.info("\n[Step 4/6] Retraining model...")
        new_model, new_metrics = self.retrain_model(train_df, val_df)
        results['new_metrics'] = new_metrics

        # Step 5: Compare performance
        logger.info("\n[Step 5/6] Comparing performance...")

        # Calculate overall improvement (weighted average)
        current_score = (
            current_metrics['sentiment_accuracy'] * 0.4 +
            current_metrics['aspect_f1'] * 0.6
        )
        new_score = (
            new_metrics['sentiment_accuracy'] * 0.4 +
            new_metrics['aspect_f1'] * 0.6
        )

        improvement = new_score - current_score
        results['improvement'] = improvement
        results['improvement_pct'] = improvement * 100

        logger.info(f"Current score: {current_score:.4f}")
        logger.info(f"New score: {new_score:.4f}")
        logger.info(f"Improvement: {improvement:+.4f} ({improvement*100:+.2f}%)")

        # Step 6: Deploy if improved
        if improvement >= self.improvement_threshold:
            logger.info("\n[Step 6/6] Deploying new model...")

            # Create version number
            version = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Save model
            self.save_model_version(new_model, version, new_metrics)

            # Deploy
            deployed = self.deploy_model(version)

            if deployed:
                results['success'] = True
                results['deployed_version'] = version
                results['message'] = f"Model retrained and deployed (v{version})"

                # Update history
                self.history.append(results)
                self._save_history()

                logger.info(f"\n{'='*80}")
                logger.info(f"SUCCESS: New model deployed (v{version})")
                logger.info(f"Improvement: {improvement*100:+.2f}%")
                logger.info(f"{'='*80}\n")
            else:
                results['message'] = "Model training successful but deployment failed"
        else:
            logger.info(f"\n[Step 6/6] Skipping deployment (insufficient improvement)")
            results['message'] = f"New model not deployed (improvement {improvement*100:.2f}% < threshold {self.improvement_threshold*100:.2f}%)"

        return results

    def get_retraining_history(self, limit: int = 10) -> List[Dict]:
        """Get recent retraining history"""
        return self.history[-limit:]


# Example usage and testing
if __name__ == "__main__":
    print("=" * 80)
    print("Model Retraining System - Test Run")
    print("=" * 80)

    # Initialize retrainer
    retrainer = ModelRetrainer(
        min_new_samples=10,  # Lower threshold for testing
        improvement_threshold=0.01
    )

    print("\n[Test 1] Checking retraining history...")
    history = retrainer.get_retraining_history()
    print(f"Retraining history: {len(history)} entries")

    print("\n[Test 2] Collecting new data...")
    new_data = retrainer.collect_new_data()
    print(f"New data samples: {len(new_data)}")

    print("\n[Test 3] Preparing training data...")
    train_df, val_df = retrainer.prepare_training_data()
    print(f"Training set: {len(train_df)} samples")
    print(f"Validation set: {len(val_df)} samples")

    if len(val_df) > 0:
        print("\n[Test 4] Evaluating current model...")
        metrics = retrainer.evaluate_model(retrainer.absa_model, val_df.head(100))
        print("\nCurrent Model Metrics:")
        for metric, value in metrics.items():
            if isinstance(value, float):
                print(f"  - {metric}: {value:.4f}")
            else:
                print(f"  - {metric}: {value}")

    print("\n" + "=" * 80)
    print("Note: To execute full retraining pipeline, call:")
    print("  retrainer.execute_retraining_pipeline(reason='Your reason here')")
    print("\nThis requires:")
    print("  1. user_feedback.csv in data/ directory")
    print("  2. Sufficient new labeled samples")
    print("  3. Performance improvement over current model")
    print("=" * 80 + "\n")
