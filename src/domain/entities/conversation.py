from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum


class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    ESCALATED = "escalated"


class IntentType(Enum):
    AGENDAR = "agendar"
    REAGENDAR = "reagendar"
    CANCELAR = "cancelar"
    CONSULTAR = "consultar"
    INFO_SERVICIOS = "info_servicios"
    SALUDO = "saludo"
    CONVERSACION_CASUAL = "conversacion_casual"
    AYUDA = "ayuda"
    OTRO = "otro"


@dataclass
class Message:
    id: Optional[str]
    conversation_id: str
    role: MessageRole
    content: str
    intent: Optional[IntentType] = None
    confidence: Optional[float] = None
    entities: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.entities is None:
            self.entities = {}
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        
        if self.content is None or not self.content.strip():
            raise ValueError("Message content cannot be empty")
        
        if self.conversation_id is None:
            raise ValueError("Conversation ID is required")


@dataclass
class Conversation:
    id: Optional[str]
    user_id: Optional[str]
    status: ConversationStatus
    current_step: str = "greeting"
    context: Dict[str, Any] = None
    messages: List[Message] = None
    created_at: datetime = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}
        if self.messages is None:
            self.messages = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def add_message(self, message: Message):
        """Add a message to the conversation"""
        if message.conversation_id != self.id:
            raise ValueError("Message conversation ID doesn't match")
        
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
        
        # Update context based on message
        if message.entities:
            self.context.update(message.entities)
    
    def get_messages_for_context(self, limit: int = 10) -> List[Dict[str, str]]:
        """Get recent messages formatted for AI context"""
        recent_messages = self.messages[-limit:] if len(self.messages) > limit else self.messages
        
        return [
            {
                "role": msg.role.value,
                "content": msg.content
            }
            for msg in recent_messages
        ]
    
    def update_step(self, step: str):
        """Update current conversation step"""
        valid_steps = [
            "greeting",
            "user_identification", 
            "service_selection",
            "appointment_scheduling",
            "confirmation",
            "completed",
            "appointment_management",
            "cancel_selection",
            "reschedule_selection",
            "reschedule_appointment_selection",
            "reminder_validation"
        ]
        
        if step not in valid_steps:
            raise ValueError(f"Invalid step: {step}")
        
        self.current_step = step
        self.updated_at = datetime.utcnow()
    
    def update_context(self, key: str, value: Any):
        """Update conversation context"""
        self.context[key] = value
        self.updated_at = datetime.utcnow()
    
    def get_context_value(self, key: str, default: Any = None) -> Any:
        """Get value from conversation context"""
        return self.context.get(key, default)
    
    def complete_conversation(self, success: bool = True):
        """Mark conversation as completed"""
        self.status = ConversationStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        if success:
            self.current_step = "completed"
    
    def escalate_conversation(self, reason: str = ""):
        """Escalate conversation to human agent"""
        self.status = ConversationStatus.ESCALATED
        self.updated_at = datetime.utcnow()
        self.context["escalation_reason"] = reason
    
    def abandon_conversation(self):
        """Mark conversation as abandoned"""
        self.status = ConversationStatus.ABANDONED
        self.updated_at = datetime.utcnow()
    
    def get_last_user_message(self) -> Optional[Message]:
        """Get the last message from user"""
        for message in reversed(self.messages):
            if message.role == MessageRole.USER:
                return message
        return None
    
    def get_last_assistant_message(self) -> Optional[Message]:
        """Get the last message from assistant"""
        for message in reversed(self.messages):
            if message.role == MessageRole.ASSISTANT:
                return message
        return None
    
    def is_active(self) -> bool:
        """Check if conversation is still active"""
        return self.status == ConversationStatus.ACTIVE
    
    def get_duration_minutes(self) -> float:
        """Get conversation duration in minutes"""
        if self.completed_at:
            end_time = self.completed_at
        else:
            end_time = datetime.utcnow()
        
        duration = end_time - self.created_at
        return duration.total_seconds() / 60
    
    def should_timeout(self, timeout_minutes: int = 30) -> bool:
        """Check if conversation should timeout due to inactivity"""
        if not self.is_active():
            return False
        
        if self.updated_at is None:
            return False
        
        inactive_duration = datetime.utcnow() - self.updated_at
        return inactive_duration.total_seconds() > (timeout_minutes * 60)


@dataclass
class ConversationSummary:
    """Summary of a completed conversation"""
    conversation_id: str
    user_id: Optional[str]
    duration_minutes: float
    total_messages: int
    final_status: ConversationStatus
    appointment_created: bool = False
    appointment_id: Optional[str] = None
    satisfaction_rating: Optional[int] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()