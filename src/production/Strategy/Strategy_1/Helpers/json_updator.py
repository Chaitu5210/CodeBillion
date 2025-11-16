from typing import Any, Dict


def json_updator(data: Dict[str, Any], score: float) -> Dict[str, Any]:
    data['final_score'] = score
    return data
