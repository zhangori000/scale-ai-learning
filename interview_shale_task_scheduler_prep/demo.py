from task_scheduler import NO_TASK_TO_RETURN, TaskServicePart1, TaskServicePart2


def run_part1_demo() -> None:
    scheduler = TaskServicePart1()
    scheduler.AddTasks([{"id": "1", "deadline": 1}, {"id": "2", "deadline": 2}])

    print("Part 1")
    print(scheduler.ConsumeTask())  # 1
    print(scheduler.ConsumeTask())  # 2
    print(scheduler.ConsumeTask())  # NO_TASK_TO_RETURN
    print()


def run_part2_demo() -> None:
    scheduler = TaskServicePart2()
    scheduler.AddTasks(
        [
            {"id": "parent", "deadline": 1, "subtasks": ["child"]},
            {"id": "child", "deadline": 5},
            {"id": "free", "deadline": 3},
        ]
    )

    print("Part 2")
    while True:
        task_id = scheduler.ConsumeTask()
        print(task_id)
        if task_id == NO_TASK_TO_RETURN:
            break


if __name__ == "__main__":
    run_part1_demo()
    run_part2_demo()
