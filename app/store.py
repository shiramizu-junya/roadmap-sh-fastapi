from itertools import count

from app.schemas.todo import TodoRead

todos: list[TodoRead] = []

# 1, 2, 3, ... と番号を1枚ずつ出す発券機。消しても番号は戻らない
todo_ids = count(1)
