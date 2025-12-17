from abc import ABC, abstractmethod
from datetime import datetime
import json
import time
from database.models import AgentLog, get_db_session

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def execute(self, input_data: dict) -> dict:
        pass
    
    def log_action(self, action: str, input_data: dict, output_data: dict, 
                   decision: str = None, success: bool = True, 
                   error_message: str = None, execution_time_ms: int = 0):
        try:
            db = get_db_session()
            log = AgentLog(
                agent_name=self.name,
                action=action,
                input_data=json.dumps(input_data) if input_data else None,
                output_data=json.dumps(output_data) if output_data else None,
                decision=decision,
                execution_time_ms=execution_time_ms,
                success=success,
                error_message=error_message
            )
            db.add(log)
            db.commit()
            db.close()
        except Exception as e:
            print(f"Error logging agent action: {e}")
    
    def run(self, input_data: dict) -> dict:
        start_time = time.time()
        try:
            result = self.execute(input_data)
            execution_time = int((time.time() - start_time) * 1000)
            self.log_action(
                action=f"{self.name}_execute",
                input_data=input_data,
                output_data=result,
                decision=result.get('decision', ''),
                success=True,
                execution_time_ms=execution_time
            )
            return result
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            self.log_action(
                action=f"{self.name}_execute",
                input_data=input_data,
                output_data=None,
                success=False,
                error_message=str(e),
                execution_time_ms=execution_time
            )
            return {"success": False, "error": str(e)}
