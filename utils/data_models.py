import secrets
import string
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import List, Optional, Any, Dict

# We remove 0, O, 1, I, L to prevent human error
# This leaves 31 characters: (31^5 = ~28.6 Million combinations)
alphabet = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"

def generate_uid():
    return ''.join(secrets.choice(alphabet) for _ in range(6))

def get_now():
    return datetime.now(timezone.utc)

@dataclass(kw_only=True)
class MasterRecord:
    uid: str = field(default_factory=generate_uid)
    mobile: str
    project: Optional[str] = None
    town_type: Optional[str] = None
    requester: Optional[str] = None
    rd_code: Optional[str] = None
    rd_name: Optional[str] = None
    town: Optional[str] = None
    state: Optional[str] = None
    designation: Optional[str] = None
    name: Optional[str] = None
    gst_no: Optional[str] = None
    email_id: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None

    def to_dict(self):
        return asdict(self)

@dataclass
class MetadataConfig:
    call_on: List[str] = field(default_factory=list)
    designations: List[str] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    modules: List[str] = field(default_factory=list)
    projects: List[str] = field(default_factory=list)
    requesters: List[str] = field(default_factory=list)
    solutions: List[str] = field(default_factory=list)
    solved_on: List[str] = field(default_factory=list)
    town_types: List[str] = field(default_factory=list)
    types: List[str] = field(default_factory=list)
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None

    def to_dict(self):
        return asdict(self)

@dataclass
class User:
    username: str
    password: str  # Hashed
    created_at: Optional[datetime] = None
    updated_by: Optional[str] = None
    updated_at: Optional[datetime] = None

    def to_dict(self):
        return asdict(self)
    
@dataclass
class EmailConfig:
    smtp_server: str
    smtp_port: int
    smtp_user: str
    smtp_password: str  # Should be stored securely
    created_by: str = ""
    created_at: datetime = field(default_factory=get_now)

    def to_dict(self):
        return asdict(self) 

@dataclass(kw_only=True)
class CallLog:
    uid: str = field(default_factory=generate_uid)
    mobile: str
    date: datetime
    project: Optional[str] = None
    town: Optional[str] = None
    requester: Optional[str] = None
    rd_code: Optional[str] = None
    rd_name: Optional[str] = None
    state: Optional[str] = None
    designation: Optional[str] = None
    name: Optional[str] = None
    module: Optional[str] = None
    issue: Optional[str] = None
    solution: Optional[str] = None
    solved_on: Optional[str] = None
    call_on: Optional[str] = None
    call_type: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None

    def to_dict(self):
        return asdict(self)

@dataclass(frozen=True)
class DateRange:
    start: Optional[datetime] = None
    end: Optional[datetime] = None           