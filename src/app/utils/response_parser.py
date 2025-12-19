# =============================== FILE PURPOSE ===============================
"""
Response Parser Utility - Parses structured agent responses into clean dictionaries for the API.

This module provides:
- parse_agent_response function: Extracts Explanation, Query Result, SQL, and Error sections from agent output
"""


def parse_agent_response(response_text: str) -> dict:
    """
    Parse the structured agent response into clean sections.
    Expected format uses delimiters: <<<EXPLANATION>>>, <<<QUERY_RESULT>>>, <<<SQL>>>, <<<ERROR>>>, <<<END>>>
    """
    result = {
        "explanation": "",
        "query_result": None,
        "sql_query": None,
        "error": None,
        "suggestions": None,
        "structured_response": None
    }
    
    if not response_text:
        return result
    
    # List of all known delimiters
    delimiters = ["<<<EXPLANATION>>>", "<<<QUERY_RESULT>>>", "<<<SQL>>>", "<<<ERROR>>>", "<<<SUGGESTIONS>>>", "<<<STRUCTURED_RESPONSE>>>", "<<<INVALID>>>", "<<<END>>>"]

    def get_section_content(marker):
        if marker not in response_text:
            return None
        start_index = response_text.find(marker) + len(marker)
        
        # Find the nearest next delimiter
        next_indices = [response_text.find(d, start_index) for d in delimiters if response_text.find(d, start_index) != -1]
        
        if next_indices:
            end_index = min(next_indices)
        else:
            end_index = len(response_text)
            
        content = response_text[start_index:end_index].strip()
        
        # Strip markdown code blocks if present
        if content.startswith("```") and content.endswith("```"):
            content = content.strip("`")
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
            
        return content

    result["explanation"] = get_section_content("<<<EXPLANATION>>>") or ""
    result["query_result"] = get_section_content("<<<QUERY_RESULT>>>")
    result["sql_query"] = get_section_content("<<<SQL>>>")
    result["error"] = get_section_content("<<<ERROR>>>") or get_section_content("<<<INVALID>>>")
    result["suggestions"] = get_section_content("<<<SUGGESTIONS>>>")
    result["structured_response"] = get_section_content("<<<STRUCTURED_RESPONSE>>>")
    
    return result
