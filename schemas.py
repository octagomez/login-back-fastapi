from pydantic import BaseModel
from typing import List

class TaskRead(BaseModel):
    id: int
    title: str
    description: str

class UserRead(BaseModel):
    id: int
    name: str
    email: str
    tasks: List[TaskRead]

