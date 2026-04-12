"""
FastAPI application module
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
import logging

from agent.agent import Agent
from config.config import Config
from api.routers.agent import router as agent_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("Starting Alees AI Agent Runtime")

    # Load configuration
    config = Config()

    # Create agent runtime
    agent = Agent(config)

    await agent.session.initialize()
    # Store inside FastAPI app state
    app.state.config = config
    app.state.agent = agent

    logger.info("Agent initialized successfully")

    yield

    logger.info("Shutting down agent runtime")

    # Optional cleanup
    if agent.session and agent.session.client:
        await agent.session.client.close()


# Create FastAPI application
def create_app():

    app = FastAPI(
        title="Alees AI Agent API",
        version="1.0",
        lifespan=lifespan
    )

    app.include_router(agent_router)

    return app


# Global app instance
app = create_app()


# Helper function to get agent
def get_agent(request: Request) -> Agent:
    return request.app.state.agent