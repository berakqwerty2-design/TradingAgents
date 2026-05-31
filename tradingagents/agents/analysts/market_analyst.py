from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from tradingagents.tools import get_stock_data, get_indicators


def get_verified_market_snapshot(
    symbol: str,
    curr_date: str = "",
    look_back_days: int = 30,
):
    """Compatibility wrapper."""
    return get_stock_data.invoke({"symbol": symbol})


def create_market_analyst(llm):
    tools = [
        get_stock_data,
        get_indicators,
    ]

    system_prompt = """You are a professional crypto and stock market analyst.
You can use these tools:
- get_stock_data
- get_indicators

Always analyze:
- trend
- momentum
- volatility
- support/resistance
- volume

Return concise but detailed analysis."""

    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt,
    )

    return agent
