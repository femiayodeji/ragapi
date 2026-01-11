from typing import Optional, List


class QueryValidator:
    def __init__(self):
        self.min_query_length = 2
    
    def validate_basic(self, query: str) -> Optional[str]:
        query_stripped = query.strip()
        
        if not query_stripped:
            return "Please provide a question."
        
        if len(query_stripped) < self.min_query_length:
            return "Your question is too short. Please provide more details."
        
        return None


validator = QueryValidator()
