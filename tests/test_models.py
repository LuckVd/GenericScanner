"""Tests for common models."""


from common.models.task import Task, TaskStatus


class TestTaskModel:
    """Tests for Task model."""

    def test_task_creation(self) -> None:
        """Test creating a task."""
        task = Task(
            name="Test Task",
            targets=["192.168.1.1"],
            policy="full",
            status=TaskStatus.PENDING,
        )

        assert task.name == "Test Task"
        assert task.targets == ["192.168.1.1"]
        assert task.policy == "full"
        assert task.status == TaskStatus.PENDING

    def test_task_progress_percent(self) -> None:
        """Test progress percentage calculation."""
        task = Task(
            name="Test Task",
            targets=["192.168.1.1"],
            progress_total=100,
            progress_completed=50,
        )

        assert task.progress_percent == 50.0

    def test_task_progress_percent_zero_total(self) -> None:
        """Test progress percentage with zero total."""
        task = Task(
            name="Test Task",
            targets=["192.168.1.1"],
            progress_total=0,
            progress_completed=0,
        )

        assert task.progress_percent == 0.0

    def test_task_to_dict(self) -> None:
        """Test task serialization."""
        task = Task(
            name="Test Task",
            targets=["192.168.1.1"],
            policy="full",
            status=TaskStatus.PENDING,
            priority=5,
        )

        data = task.to_dict()

        assert data["name"] == "Test Task"
        assert data["targets"] == ["192.168.1.1"]
        assert data["status"] == "pending"
        assert data["priority"] == 5
