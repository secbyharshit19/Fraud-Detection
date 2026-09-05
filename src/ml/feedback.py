import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

logger = logging.getLogger(__name__)

class FeedbackCollector:
    def __init__(self, feedback_dir: Optional[str] = None):
        if feedback_dir is None:
            repo_root = Path(__file__).resolve().parent.parent.parent
            self.feedback_dir = repo_root / "data" / "feedback"
        else:
            self.feedback_dir = Path(feedback_dir)
            
        self.feedback_dir.mkdir(parents=True, exist_ok=True)
        self.feedback_file = self.feedback_dir / "feedback.csv"
        
        if not self.feedback_file.exists():
            df = pd.DataFrame(columns=[
                "transaction_id", "label", "analyst_id", "notes", "timestamp"
            ])
            df.to_csv(self.feedback_file, index=False)

    def store_feedback(self, transaction_id: str, label: int, analyst_id: str, notes: str = "") -> None:
        """Stores analyst feedback for a transaction."""
        feedback_data = {
            "transaction_id": transaction_id,
            "label": label,
            "analyst_id": analyst_id,
            "notes": notes,
            "timestamp": datetime.now().isoformat()
        }
        
        df = pd.DataFrame([feedback_data])
        df.to_csv(self.feedback_file, mode='a', header=False, index=False)
        logger.info(f"Feedback stored for transaction {transaction_id}.")

    def get_feedback_stats(self) -> Dict[str, int]:
        """Returns summary of feedback labels."""
        try:
            df = pd.read_csv(self.feedback_file)
            stats = df['label'].value_counts().to_dict()
            total = len(df)
            return {
                "total_feedback": total,
                "fraud_count": stats.get(1, 0),
                "legitimate_count": stats.get(0, 0)
            }
        except Exception as e:
            logger.error(f"Error reading feedback stats: {e}")
            return {"total_feedback": 0, "fraud_count": 0, "legitimate_count": 0}

    def create_retraining_dataset(self, min_feedback_count: int = 100) -> Optional[pd.DataFrame]:
        """
        Creates a new dataset combining original data and analyst feedback,
        if sufficient feedback has been collected.
        """
        stats = self.get_feedback_stats()
        if stats["total_feedback"] < min_feedback_count:
            logger.warning(
                f"Not enough feedback for retraining. Have {stats['total_feedback']}, "
                f"need {min_feedback_count}."
            )
            return None
            
        try:
            repo_root = self.feedback_dir.parent.parent
            original_data_path = repo_root / "data" / "creditcard.csv"
            
            if not original_data_path.exists():
                logger.error("Original dataset not found.")
                return None
                
            original_df = pd.read_csv(original_data_path)
            feedback_df = pd.read_csv(self.feedback_file)
            
            # Assuming 'Time' or some other column is used as transaction_id in original data
            # Since kaggle data doesn't have an explicit transaction ID, we might need a mapping
            # For this implementation, we will append or update based on a hypothetical transaction_id match.
            # In Kaggle dataset, let's assume index is transaction_id if it's numeric
            
            # Simplified version: Just appending new verified records or updating existing
            # If transaction_id matches an index, update the label
            for _, row in feedback_df.iterrows():
                tx_id = row['transaction_id']
                label = row['label']
                try:
                    idx = int(tx_id)
                    if idx in original_df.index:
                        original_df.at[idx, 'Class'] = label
                except ValueError:
                    pass
                    
            logger.info("Retraining dataset created successfully.")
            return original_df
            
        except Exception as e:
            logger.error(f"Error creating retraining dataset: {e}")
            return None
