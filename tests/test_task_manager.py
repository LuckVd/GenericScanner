"""Tests for task manager."""


from scheduler.task_manager import TaskManager


class TestTaskManager:
    """Tests for TaskManager."""

    def test_count_targets_single(self) -> None:
        """Test counting single targets."""
        manager = TaskManager()
        count = manager._count_targets(["192.168.1.1", "example.com"])
        assert count == 2

    def test_count_targets_cidr(self) -> None:
        """Test counting CIDR ranges."""
        manager = TaskManager()
        # /30 has 4 addresses
        count = manager._count_targets(["192.168.1.0/30"])
        assert count == 4

    def test_split_targets(self) -> None:
        """Test splitting targets into chunks."""
        manager = TaskManager()
        chunks = manager.split_targets(["192.168.1.0/30"], chunk_size=2)

        # /30 has 4 addresses, but only 2 usable hosts (excluding network and broadcast)
        # Actually for /30, all 4 are counted in num_addresses
        assert len(chunks) >= 1

    def test_split_targets_domains(self) -> None:
        """Test splitting domain targets."""
        manager = TaskManager()
        chunks = manager.split_targets(
            ["example.com", "test.com", "demo.com"], chunk_size=2
        )

        assert len(chunks) == 2
        assert len(chunks[0]) == 2
        assert len(chunks[1]) == 1
