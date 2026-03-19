# Original Prompt and Translation

## English prompt

CSV to JSON Endpoint

Related Discussion
Given `users.csv` and `tasks.csv`, create an endpoint to read and parse these two CSV files into two local JSON files. Support calling GPT's API to classify one data point from one of the JSON files.

Example

Input

`users.csv` contains:

```text
id,name
1,Alice
2,Bob
```

`tasks.csv` contains:

```text
id,task
1,Task1
1,Task2
2,Task3
```

## Related discussion post translated to English

Coding interview question:

Given `users.csv` and `tasks.csv`, write an endpoint that reads the two CSV files and parses them into two local JSON files. The second part is to call GPT's API to classify one piece of data from one of the JSON files. The API part is straightforward and mostly just a simple prompt. I barely finished in time and did not have time to test it.

## Important observation

The `tasks.csv` example is slightly ambiguous:

- the `id` field appears more like a foreign key to a user than a unique task ID
- that means selecting "one data point" for classification should not rely on `id` alone

In a strong interview answer, you should notice that and propose:

- a row index
- or a generated `row_id`
- or a real `task_id` column if the schema can be changed
