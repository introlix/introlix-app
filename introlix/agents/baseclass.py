from pydantic import BaseModel

class BaseAgent(BaseModel):
    name: str = ""
    desc: str = ""

    def __init__(self, name):
        BaseModel.__init__(
            self,
            name=name
        )