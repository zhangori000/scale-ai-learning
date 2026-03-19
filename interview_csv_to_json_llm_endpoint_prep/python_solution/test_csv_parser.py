from __future__ import annotations

import unittest

from csv_parser import CSVValidationError, parse_tasks_csv, parse_users_csv


class CSVParserTest(unittest.TestCase):
    def test_parse_users_csv_adds_row_index(self) -> None:
        users_csv = b"id,name\n1,Alice\n2,Bob\n"
        users = parse_users_csv(users_csv)

        self.assertEqual(users[0].row_index, 0)
        self.assertEqual(users[1].name, "Bob")

    def test_parse_tasks_csv_adds_row_index(self) -> None:
        tasks_csv = b"id,task\n1,Task1\n1,Task2\n2,Task3\n"
        tasks = parse_tasks_csv(tasks_csv)

        self.assertEqual([task.row_index for task in tasks], [0, 1, 2])
        self.assertEqual(tasks[1].task, "Task2")

    def test_missing_header_raises(self) -> None:
        users_csv = b"id\n1\n"
        with self.assertRaises(CSVValidationError):
            parse_users_csv(users_csv)


if __name__ == "__main__":
    unittest.main()
