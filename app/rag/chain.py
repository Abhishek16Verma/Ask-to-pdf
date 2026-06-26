# LangSmith auto-traces everything once env vars are set.
# Just add RunnableConfig to make traces readable in dashboard.

from langchain_core.runnables import RunnableConfig

class LangSmithChainSetup:
    def __init__(self, settings):
        self.settings = settings

    async def invoke_chain(self, chain, inputs: dict, request_id: str, user_id: str):
        """
        Wrap chain.astream with LangSmith metadata.
        Links each trace to a specific user and request.
        """
        config = RunnableConfig(
            run_name="ask-to-pdf-query",        # visible in LangSmith UI
            metadata={
                "request_id": request_id,        # correlate with your logs
                "user_id": user_id,
                "pdf_id": inputs.get("pdf_id"),
            },
            tags=["rag", "production"],
        )
        async for chunk in chain.astream(inputs, config=config):
            yield chunk