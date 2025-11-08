"""
Supervision service for manual validation of ML predictions
"""

from datetime import datetime
from typing import List, Dict, Optional
from bson import ObjectId
from app.database.mongodb import get_database
from app.utils.logger import logger


class SupervisionService:
    """Service for handling supervision of ML predictions"""
    
    def __init__(self):
        self.db = get_database()
    
    async def get_pending_reviews(self, limit: int = 50, min_confidence: float = 0.0, max_confidence: float = 1.0) -> List[Dict]:
        """Get images pending manual review"""
        try:
            # Find classifications that are not yet reviewed and have confidence within range
            cursor = self.db.classifications.find({
                "approved": False,
                "reviewed": False,
                "predictions.tipo_prenda.confidence": {"$gte": min_confidence, "$lte": max_confidence}
            }).limit(limit)
            
            pending = []
            async for doc in cursor:
                pending.append({
                    "image_id": str(doc["_id"]),
                    "product_id": doc["product_id"],
                    "predicted_labels": doc["predictions"],
                    "confidence_avg": self._calculate_avg_confidence(doc["predictions"]),
                    "classified_at": doc["classified_at"]
                })
            
            logger.info(f"Found {len(pending)} pending reviews")
            return pending
            
        except Exception as e:
            logger.error(f"Error getting pending reviews: {e}")
            raise
    
    async def approve_prediction(self, image_id: str, reviewed_by: str, notes: Optional[str] = None) -> Dict:
        """Approve ML prediction"""
        try:
            result = await self.db.classifications.update_one(
                {"_id": ObjectId(image_id)},
                {
                    "$set": {
                        "approved": True,
                        "reviewed": True,
                        "reviewed_by": reviewed_by,
                        "reviewed_at": datetime.utcnow(),
                        "review_notes": notes,
                        "status": "approved"
                    }
                }
            )
            
            if result.modified_count == 0:
                raise ValueError(f"Image {image_id} not found or already reviewed")
            
            logger.info(f"Approved prediction for image {image_id} by {reviewed_by}")
            
            return {
                "success": True,
                "message": "Prediction approved successfully",
                "image_id": image_id,
                "status": "approved"
            }
            
        except Exception as e:
            logger.error(f"Error approving prediction: {e}")
            raise
    
    async def reject_and_correct(
        self, 
        image_id: str, 
        reviewed_by: str, 
        corrected_labels: Dict[str, str],
        notes: Optional[str] = None
    ) -> Dict:
        """Reject prediction and save corrections"""
        try:
            # Get original prediction
            original = await self.db.classifications.find_one({"_id": ObjectId(image_id)})
            if not original:
                raise ValueError(f"Image {image_id} not found")
            
            # Calculate corrections made
            corrections_made = len(corrected_labels)
            
            # Update with corrections
            result = await self.db.classifications.update_one(
                {"_id": ObjectId(image_id)},
                {
                    "$set": {
                        "approved": False,
                        "reviewed": True,
                        "reviewed_by": reviewed_by,
                        "reviewed_at": datetime.utcnow(),
                        "corrected_labels": corrected_labels,
                        "review_notes": notes,
                        "status": "rejected",
                        "corrections_count": corrections_made
                    }
                }
            )
            
            if result.modified_count == 0:
                raise ValueError(f"Failed to update image {image_id}")
            
            logger.info(f"Rejected and corrected prediction for image {image_id} by {reviewed_by}")
            
            return {
                "success": True,
                "message": f"Prediction rejected and {corrections_made} corrections saved",
                "image_id": image_id,
                "status": "rejected"
            }
            
        except Exception as e:
            logger.error(f"Error rejecting prediction: {e}")
            raise
    
    async def get_review_history(self, limit: int = 100, status: Optional[str] = None) -> List[Dict]:
        """Get history of reviews"""
        try:
            query = {"reviewed": True}
            if status:
                query["status"] = status
            
            cursor = self.db.classifications.find(query).sort("reviewed_at", -1).limit(limit)
            
            history = []
            async for doc in cursor:
                history.append({
                    "image_id": str(doc["_id"]),
                    "product_id": doc["product_id"],
                    "status": doc.get("status", "unknown"),
                    "reviewed_by": doc.get("reviewed_by", "unknown"),
                    "reviewed_at": doc.get("reviewed_at"),
                    "confidence_avg": self._calculate_avg_confidence(doc.get("predictions", {})),
                    "corrections_made": doc.get("corrections_count", 0)
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting review history: {e}")
            raise
    
    async def get_metrics(self) -> Dict:
        """Get supervision metrics"""
        try:
            # Count by status
            total_pending = await self.db.classifications.count_documents({"reviewed": False})
            total_approved = await self.db.classifications.count_documents({"status": "approved"})
            total_rejected = await self.db.classifications.count_documents({"status": "rejected"})
            
            # Calculate average confidence for approved/rejected
            approved_docs = self.db.classifications.find({"status": "approved"})
            rejected_docs = self.db.classifications.find({"status": "rejected"})
            
            approved_confidences = []
            async for doc in approved_docs:
                approved_confidences.append(self._calculate_avg_confidence(doc.get("predictions", {})))
            
            rejected_confidences = []
            async for doc in rejected_docs:
                rejected_confidences.append(self._calculate_avg_confidence(doc.get("predictions", {})))
            
            avg_confidence_approved = sum(approved_confidences) / len(approved_confidences) if approved_confidences else 0.0
            avg_confidence_rejected = sum(rejected_confidences) / len(rejected_confidences) if rejected_confidences else 0.0
            
            # Total corrections
            total_corrections = await self.db.classifications.count_documents({"corrections_count": {"$gt": 0}})
            
            # Approval rate
            total_reviewed = total_approved + total_rejected
            approval_rate = total_approved / total_reviewed if total_reviewed > 0 else 0.0
            
            # Ready for retraining? (need at least 100 approved images)
            ready_for_retraining = total_approved >= 100
            
            return {
                "total_pending": total_pending,
                "total_approved": total_approved,
                "total_rejected": total_rejected,
                "avg_confidence_approved": round(avg_confidence_approved, 2),
                "avg_confidence_rejected": round(avg_confidence_rejected, 2),
                "total_corrections": total_corrections,
                "approval_rate": round(approval_rate, 2),
                "ready_for_retraining": ready_for_retraining,
                "images_for_retraining": total_approved
            }
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            raise
    
    async def get_approved_for_training(self, min_images: int = 100) -> List[Dict]:
        """Get approved images ready for retraining"""
        try:
            cursor = self.db.classifications.find({
                "status": "approved",
                "used_for_training": {"$ne": True}
            }).limit(min_images)
            
            approved = []
            async for doc in cursor:
                approved.append({
                    "image_id": str(doc["_id"]),
                    "product_id": doc["product_id"],
                    "labels": self._extract_labels(doc["predictions"]),
                    "corrected_labels": doc.get("corrected_labels")
                })
            
            logger.info(f"Found {len(approved)} approved images for training")
            return approved
            
        except Exception as e:
            logger.error(f"Error getting approved images: {e}")
            raise
    
    async def mark_as_used_for_training(self, image_ids: List[str]) -> int:
        """Mark images as used in training"""
        try:
            object_ids = [ObjectId(id) for id in image_ids]
            result = await self.db.classifications.update_many(
                {"_id": {"$in": object_ids}},
                {"$set": {"used_for_training": True, "training_date": datetime.utcnow()}}
            )
            
            logger.info(f"Marked {result.modified_count} images as used for training")
            return result.modified_count
            
        except Exception as e:
            logger.error(f"Error marking images as used: {e}")
            raise
    
    def _calculate_avg_confidence(self, predictions: Dict) -> float:
        """Calculate average confidence from predictions"""
        if not predictions:
            return 0.0
        
        confidences = []
        for label_type, prediction in predictions.items():
            if isinstance(prediction, dict) and "confidence" in prediction:
                confidences.append(prediction["confidence"])
        
        return sum(confidences) / len(confidences) if confidences else 0.0
    
    def _extract_labels(self, predictions: Dict) -> Dict[str, str]:
        """Extract label values from predictions"""
        labels = {}
        for label_type, prediction in predictions.items():
            if isinstance(prediction, dict) and "label" in prediction:
                labels[label_type] = prediction["label"]
        return labels


# Singleton instance
supervision_service = SupervisionService()
