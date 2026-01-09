from typing import Optional, List


class QueryValidator:
    def __init__(self, service_name: str = "Government Services"):
        self.service_name = service_name
        self.min_similarity = 0.3
    
    def validate_clarity(self, query: str) -> Optional[str]:
        query_lower = query.lower().strip()
        
        greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "greetings"]
        if query_lower in greetings:
            return f"Hello! I'm here to help with {self.service_name}. What would you like to know?"
        
        if len(query.split()) <= 2:
            vague_patterns = ["how", "what", "tell me", "help", "info", "details"]
            if any(query_lower.startswith(pattern) for pattern in vague_patterns):
                return (
                    "Could you be more specific? For example:\n"
                    "• 'How do I apply for a birth certificate?'\n"
                    "• 'What documents do I need for passport renewal?'\n"
                    "• 'What are the fees for driver's license?'"
                )
        
        return None
    
    def validate_scope(self, docs: List, scores: List[float]) -> Optional[str]:
        if not docs or not scores:
            return self._out_of_scope_message()
        
        max_score = max(scores) if scores else 0
        if max_score < self.min_similarity:
            return self._out_of_scope_message()
        
        return None
    
    def _out_of_scope_message(self) -> str:
        return (
            f"I can only answer questions about {self.service_name}. "
            f"Your question appears to be outside my knowledge base.\n\n"
            f"I can help with:\n"
            f"• Application procedures\n"
            f"• Required documents\n"
            f"• Fees and payment\n"
            f"• Processing times\n\n"
            f"Could you ask something related to {self.service_name}?"
        )


validator = QueryValidator("Passport and Government Services")
