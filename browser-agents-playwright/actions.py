from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class ActionType(str, Enum):
    CLICK = "click"
    TYPE_TEXT = "type_text"
    PRESS_KEY = "press_key"
    SCROLL = "scroll"
    WAIT = "wait"
    COMPLETE = "complete"

class BrowserAction(BaseModel):
    action: ActionType = Field(description="The primary action to execute in the browser.")
    element_id: Optional[int] = Field(default=None, description="The integer ID of the target interactive element.")
    text_value: Optional[str] = Field(default=None, description="Text string to type if action is type_text.")
    key_stroke: Optional[str] = Field(default=None, description="Key identifier (e.g. Enter, Escape, ArrowDown) if action is press_key.")
    scroll_direction: Optional[str] = Field(default="down", description="Direction to scroll: 'up' or 'down'.")
    reasoning: str = Field(description="Step-by-step reasoning explaining why this action advances the objective.")
