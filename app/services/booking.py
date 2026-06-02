"""Interview booking extraction service."""
import json
import re
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.database import Booking


class BookingExtractor:
    """Extract and process interview booking information from conversations."""

    def __init__(self, llm_client, db: Session):
        """Initialize booking extractor.
        
        Args:
            llm_client: LLM client
            db: Database session
        """
        self.llm_client = llm_client
        self.db = db

    def extract_booking_intent(
        self,
        conversation_history: list,
        session_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Extract booking information from conversation.
        
        Args:
            conversation_history: List of message dicts with role and content
            session_id: Current session ID
            
        Returns:
            Booking info dict or None if no booking intent detected
        """
        if not conversation_history:
            return None
        
        # Prepare conversation text
        conv_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in conversation_history[-10:]  # Use last 10 messages
        ])

        prompt = f"""Analyze the following conversation and extract interview booking information if present.

CONVERSATION:
{conv_text}

Extract the following if mentioned:
- User name (full name)
- Email address
- Preferred interview date (in YYYY-MM-DD format)
- Preferred interview time (in HH:MM format, 24-hour)
- Any additional notes or requirements

Return a JSON object with these fields: {{"name": "", "email": "", "date": "", "time": "", "notes": ""}}.
If any field is not mentioned, use empty string.
If no booking intent is detected, return {{"name": "", "email": "", "date": "", "time": "", "notes": ""}}.
Return ONLY valid JSON, no additional text."""

        response = self.llm_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300,
        )

        try:
            booking_data = json.loads(response.choices[0].message.content)
            
            # Check if any booking info was extracted
            if not any([booking_data.get("name"), booking_data.get("email")]):
                return None
            
            # Validate required fields
            if not (booking_data.get("name") and booking_data.get("email")):
                return None
            
            # Validate date format
            if booking_data.get("date"):
                try:
                    datetime.strptime(booking_data["date"], "%Y-%m-%d")
                except ValueError:
                    booking_data["date"] = ""
            
            # Validate time format
            if booking_data.get("time"):
                try:
                    datetime.strptime(booking_data["time"], "%H:%M")
                except ValueError:
                    booking_data["time"] = ""
            
            return booking_data
        except json.JSONDecodeError:
            return None

    def save_booking(
        self,
        session_id: str,
        booking_data: Dict[str, Any],
    ) -> Booking:
        """Save booking information to database.
        
        Args:
            session_id: Current session ID
            booking_data: Extracted booking data
            
        Returns:
            Saved Booking instance
        """
        booking = Booking(
            conversation_id=session_id,
            user_name=booking_data.get("name", ""),
            user_email=booking_data.get("email", ""),
            interview_date=booking_data.get("date", ""),
            interview_time=booking_data.get("time", ""),
            additional_info=booking_data.get("notes", ""),
        )
        
        self.db.add(booking)
        self.db.commit()
        self.db.refresh(booking)
        
        return booking

    def get_booking_status(self, session_id: str) -> Optional[Booking]:
        """Get booking status for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Booking instance or None
        """
        booking = self.db.query(Booking).filter(
            Booking.conversation_id == session_id
        ).first()
        return booking
