from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from tradingagents.tools.stock_tools import (
    get_stock_data,
    get_indicators,
)

# =========================================================
# TOOL PATCH
# =========================================================

def get_verified_market_snapshot(
    symbol: str,
    curr_date: str,
    look_back_days: int = 30
):
    """
    Compatibility wrapper
    """

    return get_stock_data(
        symbol=symbol,
        start_date="2026-01-01",
        end_date=curr_date
    )

# =========================================================
# REGISTER TOOLS
# =========================================================

tools = [
    get_stock_data,
    get_indicators,
    get_verified_market_snapshot,
]

# =========================================================
# MARKET ANALYST NODE
# =========================================================

def market_analyst_node(state, llm):

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
You are a professional crypto and stock market analyst.

You have access ONLY to these tools:

1. get_stock_data
2. get_indicators
3. get_verified_market_snapshot

DO NOT call tools outside this list.

Always analyze carefully and provide:
- trend
- momentum
- support/resistance
- risk
- recommendation
"""
        ),
        ("human", "{messages}")
    ])

    chain = (
        prompt
        | llm.bind_tools(tools)
        | StrOutputParser()
    )

    result = chain.invoke({
        "messages": state["messages"]
    })

    return {
        "messages": [result]
    }
