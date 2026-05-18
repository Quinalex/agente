"""
Reflection Agent - Evaluate and improve execution results.
"""

import json
import logging
from typing import Dict, Any

from app.agents.base import BaseAgent, AgentState
from app.llm.client import llm_client

logger = logging.getLogger(__name__)


class ReflectionAgent(BaseAgent):
    """Agent that reflects on results and suggests improvements."""

    def __init__(self):
        super().__init__("ReflectionAgent", model="gpt-4-turbo")

    async def execute(self, state: AgentState) -> Dict[str, Any]:
        """Evaluate the execution results."""
        logger.info("Reflecting on execution")

        if not state.results:
            return {"is_complete": True, "feedback": "No results to evaluate"}

        # Analyze results
        reflection_prompt = f"""
        Evaluate the execution results for task: {state.task}
        
        Results:
        {json.dumps(state.results, indent=2)}
        
        Analyze:
        1. Were the objectives achieved?
        2. Are there any errors or failures?
        3. What improvements could be made?
        4. Is the task complete? (yes/no)
        
        Return JSON:
        {{
            "is_complete": boolean,
            "success_rate": 0-100,
            "issues": ["..."],
            "feedback": "...",
            "suggestions": ["..."]
        }}
        """

        messages = state.messages + [{"role": "user", "content": reflection_prompt}]

        response = await llm_client.complete(
            messages=messages,
            temperature=0.5,
            max_tokens=1000,
        )

        await self.message("reflection", response)

        # Parse reflection
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                reflection_json = response[json_start:json_end]
                reflection = json.loads(reflection_json)
            else:
                reflection = {"is_complete": True, "feedback": response}
        except json.JSONDecodeError:
            logger.warning("Failed to parse reflection JSON")
            reflection = {"is_complete": True, "feedback": response}

        return reflection
