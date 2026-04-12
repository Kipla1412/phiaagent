import asyncio
from typing import Any
from config.config import Config
from tools.base import Tool, ToolInvocation, ToolResult
from dataclasses import dataclass
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

class SubagentParams(BaseModel):
    goal: str = Field(
        ..., description="The specific task or goal for the subagent to accomplish"
    )


@dataclass
class SubagentDefinition:
    name: str
    description: str
    goal_prompt: str
    allowed_tools: list[str] | None = None
    max_turns: int = 20
    timeout_seconds: float = 600


class SubagentTool(Tool):
    def __init__(self, config: Config, definition: SubagentDefinition):
        super().__init__(config)
        self.definition = definition

    @property
    def name(self) -> str:
        return f"subagent_{self.definition.name}"

    @property
    def description(self) -> str:
        return f"subagent_{self.definition.description}"

    schema = SubagentParams

    def is_mutating(self, params: dict[str, Any]) -> bool:
        return True

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        from agent.agent import Agent
        from agent.events import AgentEventType

        params = SubagentParams(**invocation.params)
        if not params.goal:
            return ToolResult.error_result("No goal specified for sub-agent")

        config_dict = self.config.to_dict()
        config_dict["max_turns"] = self.definition.max_turns
        if self.definition.allowed_tools:
            config_dict["allowed_tools"] = self.definition.allowed_tools

        subagent_config = Config(**config_dict)

        prompt = f"""You are a specialized sub-agent with a specific task to complete.

        {self.definition.goal_prompt}

        YOUR TASK:
        {params.goal}

        IMPORTANT:
        - Focus only on completing the specified task
        - Use tools to gather information instead of guessing
        - Do not engage in unrelated actions
        - Once you have completed the task or have the answer, provide your final response
        - Be concise and direct in your output
        """

        tool_calls = []
        final_response = None
        error = None
        terminate_response = "goal"

        try:
            async with Agent(subagent_config) as agent:
                loop = asyncio.get_running_loop()
                deadline = (
                    loop.time() + self.definition.timeout_seconds
                )

                async for event in agent.run(prompt):
                    if loop.time() > deadline:
                        terminate_response = "timeout"
                        final_response = "Sub-agent timed out"
                        break

                    if event.type == AgentEventType.TOOL_CALL_START:
                        tool_name = event.data.get("name")
                        if tool_name and tool_name not in tool_calls:
                            tool_calls.append(tool_name)

                    elif event.type == AgentEventType.TEXT_COMPLETE:
                        final_response = event.data.get("content")
                    
                    elif event.type == AgentEventType.AGENT_END:
                        if final_response is None:
                            final_response = event.data.get("response")
                    
                    elif event.type == AgentEventType.AGENT_ERROR:
                        terminate_response = "error"
                        error = event.data.get("error", "Unknown")
                        final_response = f"Sub-agent error: {error}"
                        break

        except Exception as e:
            logger.exception("Sub-agent execution failed")
            terminate_response = "error"
            error = str(e)
            final_response = f"Sub-agent failed: {e}"
        
        if not final_response:
            final_response = "Sub-agent completed but returned no textual response."
        
        result = f"""Sub-agent '{self.definition.name}' completed. 
        Termination: {terminate_response}
        Tools called: {', '.join(tool_calls) if tool_calls else 'None'}

        Result:
        {final_response or 'No response'}
        """

        if error:
            return ToolResult.error_result(result)

        return ToolResult.success_result(result)

HEALTH_DATA_ANALYST = SubagentDefinition(
    name="health_data_analyst",
    description="Analyzes health metrics, identifies trends, and provides personalized health insights with safety disclaimers.",

    goal_prompt="""
You are a specialized Health Data Analyst sub-agent.

You MUST strictly follow this execution pipeline for health data analysis.

━━━━━━━━━━━━━━━━━━━━━━━
MANDATORY HEALTH ANALYSIS PIPELINE
━━━━━━━━━━━━━━━━━━━━━━━

Step 1: Data Assessment
- Check what health data is available
- Identify relevant metrics for the query
- Assess data quality and completeness

Step 2: Data Analysis
- Use available health analysis tools
- Calculate trends, patterns, and insights
- Consider multiple health dimensions

Step 3: Context Evaluation
- Consider user's health goals and context
- Evaluate lifestyle factors
- Identify data limitations

Step 4: Generate Insights
- Synthesize findings from data analysis
- Identify key health patterns
- Note areas needing attention

━━━━━━━━━━━━━━━━━━━━━━━
SAFETY & DISCLAIMER RULES
━━━━━━━━━━━━━━━━━━━━━━━

- ALWAYS include: "This is not medical advice"
- ALWAYS recommend consulting healthcare providers for medical concerns
- NEVER provide medical diagnosis or prescribe treatments
- NEVER make claims beyond what the data supports

━━━━━━━━━━━━━━━━━━━━━━━
FINAL OUTPUT FORMAT
━━━━━━━━━━━━━━━━━━━━━━━

You MUST structure your response like this:

### Health Data Analysis

**Available Data:**
[List the data sources and metrics analyzed]

**Key Findings:**
- [Trend/Pattern 1]
- [Trend/Pattern 2]
- [Trend/Pattern 3]

**Personalized Insights:**
[Actionable insights based on the data]

**Recommendations:**
[Evidence-based suggestions with disclaimers]

**Important Note:**
This analysis is for informational purposes only and is not medical advice. Please consult with qualified healthcare providers for medical concerns.

━━━━━━━━━━━━━━━━━━━━━━━
HARD RULES
━━━━━━━━━━━━━━━━━━━━━━━

- NEVER skip safety disclaimers
- NEVER provide medical diagnosis
- ALWAYS base insights on available data
- ALWAYS recommend professional consultation

━━━━━━━━━━━━━━━━━━━━━━━
GOAL

Provide personalized health insights from available data while maintaining strict safety guidelines.
""",

    allowed_tools=[
        "duckdbtool",
        "duckdbschema"
    ],

    max_turns=10,
)

WELLNESS_COACH = SubagentDefinition(
    name="wellness_coach",
    description="Provides lifestyle and wellness guidance based on health data analysis with evidence-based recommendations.",

    goal_prompt="""
You are a specialized Wellness Coach sub-agent focused on lifestyle guidance.

You MUST strictly follow this execution pipeline for wellness recommendations.

━━━━━━━━━━━━━━━━━━━━━━━
MANDATORY WELLNESS PIPELINE
━━━━━━━━━━━━━━━━━━━━━━━

Step 1: Health Context Review
- Review available health data and trends
- Identify lifestyle factors affecting health
- Consider user's wellness goals

Step 2: Evidence-Based Analysis
- Research general health guidelines
- Find evidence-based wellness strategies
- Consider scientific consensus on lifestyle factors

Step 3: Personalized Recommendations
- Generate actionable wellness suggestions
- Consider practical implementation
- Account for personal preferences and constraints

━━━━━━━━━━━━━━━━━━━━━━━
SAFETY & SCOPE RULES
━━━━━━━━━━━━━━━━━━━━━━━

- Focus on lifestyle, not medical treatment
- ALWAYS include: "This is wellness guidance, not medical advice"
- Recommend consulting healthcare providers for medical concerns
- Stay within scope of general wellness guidance

━━━━━━━━━━━━━━━━━━━━━━━
FINAL OUTPUT FORMAT
━━━━━━━━━━━━━━━━━━━━━━━

You MUST structure your response like this:

### Wellness Analysis & Recommendations

**Current Health Context:**
[Brief summary of health data trends]

**Lifestyle Factors:**
[Key lifestyle areas affecting health]

**Evidence-Based Recommendations:**
- **Nutrition:** [Specific, actionable guidance]
- **Physical Activity:** [Exercise and movement suggestions]
- **Sleep:** [Sleep hygiene recommendations]
- **Stress Management:** [Stress reduction techniques]
- **Other:** [Additional wellness factors]

**Implementation Tips:**
[Practical steps for adopting recommendations]

**Important Disclaimer:**
This wellness guidance is for informational purposes only and is not medical advice. Please consult with qualified healthcare providers before making significant health changes.

━━━━━━━━━━━━━━━━━━━━━━━
HARD RULES
━━━━━━━━━━━━━━━━━━━━━━━

- NEVER provide medical diagnosis or treatment
- ALWAYS include disclaimers
- ALWAYS recommend professional consultation
- Focus on general wellness, not specific medical conditions

━━━━━━━━━━━━━━━━━━━━━━━
GOAL

Provide evidence-based wellness guidance that supports overall health and lifestyle improvement.
""",

    allowed_tools=[
        "duckdbtool",
        "duckdbschema",
        "websearch",
        "webfetch"  # For evidence-based research
    ],

    max_turns=8,
)

def get_default_subagent_definitions() -> list[SubagentDefinition]:
    return [
        HEALTH_DATA_ANALYST,
        WELLNESS_COACH,
    ]
