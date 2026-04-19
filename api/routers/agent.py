# from fastapi import APIRouter, Request
# from fastapi.responses import StreamingResponse
# from pydantic import BaseModel
# import json

# router = APIRouter(prefix="/agent")


# class ChatRequest(BaseModel):
#     message: str


# @router.post("/chat")
# async def chat(req: ChatRequest, request: Request):

#     agent = request.app.state.agent

#     async def event_stream():

#         async for event in agent.run(req.message):

#             yield json.dumps({
#                 "type": event.type.value if hasattr(event.type, "value") else str(event.type),
#                 "data": event.data
#             }) + "\n"

#     return StreamingResponse(
#         event_stream(),
#         media_type="application/json"
#     )

from fastapi import APIRouter, Request, Depends
from api.auth import get_current_user, require_permission
from pydantic import BaseModel, Field
from fastapi.responses import StreamingResponse
import json
import uuid
from typing import Optional

from agent.agent import Agent

router = APIRouter(prefix="/agent")


class HealthInsightRequest(BaseModel):
    message: str = Field(..., description="Health-related question or data analysis request")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    health_data_context: Optional[dict] = Field(None, description="Optional health data context")


# class HealthDataUploadRequest(BaseModel):
#     data_type: str = Field(..., description="Type of health data (exercise, sleep, nutrition, etc.)")
#     data: dict = Field(..., description="Health data to be analyzed")
#     session_id: Optional[str] = Field(None, description="Session ID")


@router.post(
    "/phiaagent",
    summary="Personal Health Insight Assistant",
    description="""
Get personalized health insights and analysis from your health data.

This endpoint processes health-related queries and provides:
- Data-driven health insights
- Trend analysis from your health metrics
- Evidence-based wellness recommendations
- Safety-focused guidance with medical disclaimers

Authentication:
Requires a valid authenticated user session.

Permission Required:
`phiaagent:analyze`
""",
    dependencies=[Depends(require_permission("phiaagent", "analyze"))]
)
async def analyze_health(req: HealthInsightRequest, request: Request):

    sessions = request.app.state.sessions
    config = request.app.state.config

    user = request.state.user
    # Generate session id if missing
    user_id = user.get("sub")
    session_id = req.session_id or str(uuid.uuid4())

    # Add health context to message if provided
    enhanced_message = req.message
    if req.health_data_context:
        enhanced_message = f"""
Health Context: {json.dumps(req.health_data_context)}
User Query: {req.message}
"""

    if user_id not in sessions:
        agent = Agent(config)
        await agent.__aenter__()
        sessions[user_id] = agent

    agent = sessions[user_id]

    async def health_insight_stream():
        async for event in agent.run(enhanced_message):
            yield json.dumps({
                "type": event.type.value if hasattr(event.type, "value") else str(event.type),
                "data": event.data,
                "session_id": session_id,
                "insight_type": "health_analysis"
            }) + "\n"

    return StreamingResponse(
        health_insight_stream(),
        media_type="application/json; charset=utf-8",
        headers={
            "X-Session-ID": session_id,
            "X-Content-Type": "health-insight"
        }
    )


# @router.post(
#     "/wellness-coach",
#     summary="Wellness Coaching & Guidance",
#     description="""
# Get personalized wellness coaching and lifestyle guidance.

# This endpoint provides:
# - Evidence-based wellness recommendations
# - Lifestyle improvement suggestions
# - Health goal setting support
# - Preventive health guidance

# Wellness Areas:
# - Nutrition coaching
# - Exercise planning
# - Sleep hygiene
# - Stress management
# - Healthy habit formation

# Safety Features:
# - Medical disclaimers included
# - No medical diagnosis provided
# - Recommends professional consultation
# - Evidence-based guidance only

# Authentication:
# Requires a valid authenticated user session.

# Permission Required:
# `health-assistant:wellness`
# """,
#     dependencies=[Depends(require_permission("health-assistant", "wellness"))]
# )
# async def wellness_coaching(req: HealthInsightRequest, request: Request):

#     sessions = request.app.state.sessions
#     config = request.app.state.config

#     user = request.state.user
#     user_id = user.get("sub")
#     session_id = req.session_id or str(uuid.uuid4())

#     # Add wellness coaching context
#     coaching_message = f"""
# Wellness Coaching Request: {req.message}

# Please provide evidence-based wellness guidance with the following structure:
# 1. Current Health Context Analysis
# 2. Evidence-Based Recommendations
# 3. Implementation Tips
# 4. Safety Disclaimer
# """

#     if user_id not in sessions:
#         agent = Agent(config)
#         await agent.__aenter__()
#         sessions[user_id] = agent

#     agent = sessions[user_id]

#     async def wellness_stream():
#         async for event in agent.run(coaching_message):
#             yield json.dumps({
#                 "type": event.type.value if hasattr(event.type, "value") else str(event.type),
#                 "data": event.data,
#                 "session_id": session_id,
#                 "insight_type": "wellness_coaching"
#             }) + "\n"

#     return StreamingResponse(
#         wellness_stream(),
#         media_type="application/json; charset=utf-8",
#         headers={
#             "X-Session-ID": session_id,
#             "X-Content-Type": "wellness-guidance"
#         }
#     )


# @router.post(
#     "/data-insights",
#     summary="Health Data Analysis",
#     description="""
# Analyze specific health data and generate insights.

# This endpoint processes structured health data and provides:
# - Statistical analysis of health metrics
# - Trend identification
# - Pattern recognition
# - Data quality assessment

# Supported Data Types:
# - Exercise and activity logs
# - Sleep patterns
# - Nutrition data
# - Biometric measurements
# - Wellness tracking data

# Analysis Features:
# - DuckDB-powered data analysis
# - Statistical trend calculation
# - Pattern identification
# - Quality assessment

# Authentication:
# Requires a valid authenticated user session.

# Permission Required:
# `health-assistant:data-analysis`
# """,
#     dependencies=[Depends(require_permission("health-assistant", "data-analysis"))]
# )
# async def health_data_insights(req: HealthDataUploadRequest, request: Request):

#     sessions = request.app.state.sessions
#     config = request.app.state.config

#     user = request.state.user
#     user_id = user.get("sub")
#     session_id = req.session_id or str(uuid.uuid4())

#     # Create data analysis message
#     analysis_message = f"""
# Please analyze the following {req.data_type} health data:

# Data: {json.dumps(req.data, indent=2)}

# Provide:
# 1. Data Quality Assessment
# 2. Statistical Summary
# 3. Trend Analysis
# 4. Key Insights
# 5. Recommendations

# Remember to include appropriate medical disclaimers.
# """

#     if user_id not in sessions:
#         agent = Agent(config)
#         await agent.__aenter__()
#         sessions[user_id] = agent

#     agent = sessions[user_id]

#     async def data_analysis_stream():
#         async for event in agent.run(analysis_message):
#             yield json.dumps({
#                 "type": event.type.value if hasattr(event.type, "value") else str(event.type),
#                 "data": event.data,
#                 "session_id": session_id,
#                 "data_type": req.data_type,
#                 "insight_type": "data_analysis"
#             }) + "\n"

#     return StreamingResponse(
#         data_analysis_stream(),
#         media_type="application/json; charset=utf-8",
#         headers={
#             "X-Session-ID": session_id,
#             "X-Data-Type": req.data_type,
#             "X-Content-Type": "health-data-insights"
#         }
#     )


# @router.get(
#     "/session/{session_id}",
#     summary="Get Health Session Info",
#     description="""
# Get information about a health analysis session.

# Returns session metadata and conversation history for health tracking.
# """,
#     dependencies=[Depends(require_permission("health-assistant", "session-info"))]
# )
# async def get_health_session(session_id: str, request: Request):
#     user = request.state.user
#     user_id = user.get("sub")
    
#     sessions = request.app.state.sessions
    
#     if user_id not in sessions:
#         return {"error": "No active session found"}
    
#     return {
#         "session_id": session_id,
#         "user_id": user_id,
#         "session_type": "health_analysis",
#         "status": "active",
#         "capabilities": [
#             "health_data_analysis",
#             "wellness_coaching", 
#             "trend_analysis",
#             "evidence_based_guidance"
#         ]
#     }


# # Legacy endpoint for backward compatibility
# @router.post(
#     "/consultagent",
#     summary="Legacy Agent Chat (Deprecated)",
#     description="""
# Legacy endpoint for backward compatibility. 
# Use /analyze instead.
# """,
#     dependencies=[Depends(require_permission("health-assistant", "legacy"))]
# )
# async def legacy_chat(req: HealthInsightRequest, request: Request):
#     return await analyze_health(req, request)
