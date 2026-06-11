class LocalizationService:
    """Stub for future AI-powered localization.

    ``localize_chunk`` will call the LLM client to translate each chunk
    using its rolling memory and game context.
    """

    @staticmethod
    async def localize_chunk(
        chunk_id: int,
        project_id: int,
    ) -> None:
        raise NotImplementedError("AI localization is not yet implemented")
