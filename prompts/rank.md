# Rank Prompt

Score candidate items for the user's DeepBrief profile.

Return only the structured output requested by the caller. Score each item from 0 to 100 and
include one concise sentence of justification. Apply learned preferences and ratings history
as modifiers, but never resurface items already marked processed.

Budget discipline: keep the response compact and stop once the required schema is complete.
