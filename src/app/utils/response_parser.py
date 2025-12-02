"""
Utility module for parsing agent responses.
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
        "error": None
    }
    
    if not response_text:
        return result
    
    # Extract EXPLANATION section
    if "<<<EXPLANATION>>>" in response_text and "<<<" in response_text[response_text.find("<<<EXPLANATION>>>") + 17:]:
        start = response_text.find("<<<EXPLANATION>>>") + 17
        # Find the next delimiter
        next_delimiters = ["<<<QUERY_RESULT>>>", "<<<SQL>>>", "<<<ERROR>>>", "<<<INVALID>>>", "<<<END>>>"]
        end_positions = [response_text.find(d, start) for d in next_delimiters if response_text.find(d, start) != -1]
        end = min(end_positions) if end_positions else len(response_text)
        result["explanation"] = response_text[start:end].strip()
    
    # Extract QUERY_RESULT section (markdown table)
    if "<<<QUERY_RESULT>>>" in response_text:
        start = response_text.find("<<<QUERY_RESULT>>>") + 18
        end = response_text.find("<<<END>>>", start) if "<<<END>>>" in response_text[start:] else len(response_text)
        result["query_result"] = response_text[start:end].strip()
    
    # Extract SQL section
    if "<<<SQL>>>" in response_text:
        start = response_text.find("<<<SQL>>>") + 9
        end = response_text.find("<<<END>>>", start) if "<<<END>>>" in response_text[start:] else len(response_text)
        result["sql_query"] = response_text[start:end].strip()
    
    # Extract ERROR section
    if "<<<ERROR>>>" in response_text:
        start = response_text.find("<<<ERROR>>>") + 11
        end = response_text.find("<<<END>>>", start) if "<<<END>>>" in response_text[start:] else len(response_text)
        result["error"] = response_text[start:end].strip()
    
    # Extract INVALID section (treated as error)
    if "<<<INVALID>>>" in response_text:
        start = response_text.find("<<<INVALID>>>") + 13
        end = response_text.find("<<<END>>>", start) if "<<<END>>>" in response_text[start:] else len(response_text)
        result["error"] = response_text[start:end].strip()
    
    return result
