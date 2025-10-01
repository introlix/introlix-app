# Steps of how this will work
# 1. User provides a prompt
# 2. Context agent asks questions to clarify the prompt and make a enhnaced prompt
# 3. Planner agent breaks down the prompt into sub-tasks and creates a plan amd also create search keywords for explorer agent
# 4. Explorer agent searches the web for relevant information using the search keywords and returns the answers written by LLM
# 5. Verifier agent verifies the information provided by explorer agent and return the verified information and also the sources used to verify the information
# 6. Researcher agent synthesizes the verified information into a comprehensive research output
# 7. Writer agent creates a well-structured written document based on the research output
# 8. User gets the final output


# Note: When verifer agent rejects any information then user will be see the rejected information and if agent have done any mistake then user can correct it.