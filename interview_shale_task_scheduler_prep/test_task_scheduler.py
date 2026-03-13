import unittest

from task_scheduler import NO_TASK_TO_RETURN, TaskServicePart1, TaskServicePart2


class Part1Tests(unittest.TestCase):
    def test_consume_empty(self) -> None:
        scheduler = TaskServicePart1()
        self.assertEqual(scheduler.ConsumeTask(), NO_TASK_TO_RETURN)

    def test_returns_smallest_deadline_and_removes_task(self) -> None:
        scheduler = TaskServicePart1()
        scheduler.AddTasks(
            [
                {"id": "1", "deadline": 1},
                {"id": "2", "deadline": 2},
            ]
        )

        self.assertEqual(scheduler.ConsumeTask(), "1")
        self.assertEqual(scheduler.ConsumeTask(), "2")
        self.assertEqual(scheduler.ConsumeTask(), NO_TASK_TO_RETURN)

    def test_tie_breaks_by_insertion_order(self) -> None:
        scheduler = TaskServicePart1()
        scheduler.AddTasks(
            [
                {"id": "a", "deadline": 3},
                {"id": "b", "deadline": 3},
                {"id": "c", "deadline": 3},
            ]
        )

        self.assertEqual(scheduler.ConsumeTask(), "a")
        self.assertEqual(scheduler.ConsumeTask(), "b")
        self.assertEqual(scheduler.ConsumeTask(), "c")


class Part2Tests(unittest.TestCase):
    def test_nested_subtasks_must_finish_before_parent(self) -> None:
        scheduler = TaskServicePart2()
        scheduler.AddTasks(
            [
                {
                    "id": "A",
                    "deadline": 10,
                    "subtasks": [
                        {
                            "id": "B",
                            "deadline": 2,
                            "subtasks": [{"id": "C", "deadline": 1}],
                        }
                    ],
                }
            ]
        )

        self.assertEqual(scheduler.ConsumeTask(), "C")
        self.assertEqual(scheduler.ConsumeTask(), "B")
        self.assertEqual(scheduler.ConsumeTask(), "A")
        self.assertEqual(scheduler.ConsumeTask(), NO_TASK_TO_RETURN)

    def test_subtasks_as_ids_are_supported(self) -> None:
        scheduler = TaskServicePart2()
        scheduler.AddTasks(
            [
                {"id": "parent", "deadline": 1, "subtasks": ["child"]},
                {"id": "child", "deadline": 5, "subtasks": []},
            ]
        )

        # Parent has earlier deadline but is blocked on child.
        self.assertEqual(scheduler.ConsumeTask(), "child")
        self.assertEqual(scheduler.ConsumeTask(), "parent")

    def test_no_eligible_task_until_missing_dependency_is_defined(self) -> None:
        scheduler = TaskServicePart2()
        scheduler.AddTasks([{"id": "P", "deadline": 1, "subtasks": ["X"]}])
        self.assertEqual(scheduler.ConsumeTask(), NO_TASK_TO_RETURN)

        scheduler.AddTasks([{"id": "X", "deadline": 3}])
        self.assertEqual(scheduler.ConsumeTask(), "X")
        self.assertEqual(scheduler.ConsumeTask(), "P")

    def test_returns_earliest_among_currently_eligible_tasks(self) -> None:
        scheduler = TaskServicePart2()
        scheduler.AddTasks(
            [
                {"id": "blocked_parent", "deadline": 1, "subtasks": ["dep"]},
                {"id": "free", "deadline": 2},
                {"id": "dep", "deadline": 5},
            ]
        )

        self.assertEqual(scheduler.ConsumeTask(), "free")
        self.assertEqual(scheduler.ConsumeTask(), "dep")
        self.assertEqual(scheduler.ConsumeTask(), "blocked_parent")

    def test_cycle_means_nothing_is_eligible(self) -> None:
        scheduler = TaskServicePart2()
        scheduler.AddTasks(
            [
                {"id": "A", "deadline": 1, "subtasks": ["B"]},
                {"id": "B", "deadline": 2, "subtasks": ["A"]},
            ]
        )

        self.assertEqual(scheduler.ConsumeTask(), NO_TASK_TO_RETURN)


if __name__ == "__main__":
    unittest.main()
