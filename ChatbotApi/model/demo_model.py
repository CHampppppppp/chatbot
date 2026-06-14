from pydantic.main import BaseModel


class DemoModel(BaseModel):
    width: int
    height: int
