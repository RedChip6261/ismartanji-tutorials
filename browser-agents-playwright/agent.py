import asyncio
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field
from playwright.async_api import async_playwright, Page

class ActionType(str, Enum):
    CLICK = "click"
    TYPE_TEXT = "type_text"
    PRESS_KEY = "press_key"
    SCROLL = "scroll"
    WAIT = "wait"
    COMPLETE = "complete"

class BrowserAction(BaseModel):
    action: ActionType
    element_id: Optional[int] = Field(default=None, description="Numeric element identifier")
    text_value: Optional[str] = Field(default=None, description="Text to enter")
    key_stroke: Optional[str] = Field(default=None, description="Keyboard key to press")
    scroll_direction: Optional[str] = Field(default="down", description="Scroll direction: up or down")
    reasoning: str = Field(description="Step-by-step reasoning for this action")

class AutonomousBrowserAgent:
    def __init__(self, page: Page, max_steps: int = 15):
        self.page = page
        self.max_steps = max_steps
        self.element_registry: Dict[int, str] = {}

    async def extract_interactive_state(self) -> str:
        """
        Extracts visible interactive elements from the live page,
        assigns deterministic numeric IDs, and constructs a pruned textual state.
        """
        self.element_registry.clear()
        
        discovery_script = """
        () => {
            const elements = Array.from(document.querySelectorAll(
                'a, button, input, select, textarea, [role="button"], [tabindex="0"]'
            ));
            return elements.filter(el => {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
            }).map((el, index) => {
                el.setAttribute('data-agent-id', index);
                return {
                    id: index,
                    tag: el.tagName.toLowerCase(),
                    role: el.getAttribute('role') || el.tagName.toLowerCase(),
                    text: (el.innerText || el.getAttribute('aria-label') || el.getAttribute('placeholder') || '').trim().substring(0, 80),
                    selector: `[data-agent-id="${index}"]`
                };
            });
        }
        """
        raw_elements = await self.page.evaluate(discovery_script)
        state_lines = [f"Current URL: {self.page.url}", "Interactive Elements on Screen:"]
        
        for item in raw_elements:
            self.element_registry[item['id']] = item['selector']
            clean_text = item['text'].replace('\n', ' ')
            state_lines.append(f"  [{item['id']}] <{item['tag']}> role='{item['role']}' text='{clean_text}'")
            
        return "\n".join(state_lines)

    async def execute_action(self, action: BrowserAction) -> bool:
        """Executes the validated action on the Playwright page."""
        print(f"Executing: {action.action.value} on element {action.element_id} | Reasoning: {action.reasoning}")
        
        if action.action == ActionType.COMPLETE:
            return True
            
        if action.action == ActionType.CLICK and action.element_id is not None:
            selector = self.element_registry.get(action.element_id)
            if selector:
                await self.page.click(selector, timeout=5000)
                await self.page.wait_for_load_state("networkidle", timeout=5000)
                
        elif action.action == ActionType.TYPE_TEXT and action.element_id is not None:
            selector = self.element_registry.get(action.element_id)
            if selector and action.text_value:
                await self.page.fill(selector, action.text_value)
                
        elif action.action == ActionType.PRESS_KEY and action.key_stroke:
            await self.page.keyboard.press(action.key_stroke)
            
        elif action.action == ActionType.SCROLL:
            delta = 600 if action.scroll_direction == "down" else -600
            await self.page.mouse.wheel(0, delta)
            await asyncio.sleep(0.5)
            
        elif action.action == ActionType.WAIT:
            await asyncio.sleep(2.0)
            
        return False

async def run_automation():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()
        
        agent = AutonomousBrowserAgent(page)
        await page.goto("https://ismartanji.com")
        
        for step in range(agent.max_steps):
            state_repr = await agent.extract_interactive_state()
            print(f"--- Step {step + 1} State Extracted ({len(agent.element_registry)} nodes) ---")
            
            # Simulated structured decision advancing the workflow
            simulated_decision = BrowserAction(
                action=ActionType.WAIT,
                reasoning="Allowing asynchronous SPA client bundles to hydrate before interaction."
            )
            
            is_finished = await agent.execute_action(simulated_decision)
            if is_finished:
                print("Task successfully completed.")
                break
                
            await asyncio.sleep(1.0)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_automation())
