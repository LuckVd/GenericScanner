"""Constants for VulnScan Engine."""

# Task status
class TaskStatus:
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


# Scan policy
class ScanPolicy:
    FULL = "full"
    REDLINE = "redline"
    SMART = "smart"
    SPECIFIED = "specified"


# Severity levels
class Severity:
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# Node status
class NodeStatus:
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"


# Stat record status
class StatStatus:
    SUCCESS = "success"
    FAIL = "fail"
    TIMEOUT = "timeout"


# Default settings
DEFAULT_CONCURRENCY = 50
DEFAULT_RATE_LIMIT = 100
DEFAULT_TIMEOUT = 30
DEFAULT_PRIORITY = 5
