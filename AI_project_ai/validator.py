import json
from pydantic import ValidationError
from schemas import Bedrijfsprofiel

def valideer_llm_output(raw_content: str):
    """
    Schoont de LLM output op en valideert tegen het Bedrijfsprofiel schema.
    Geeft (dict, None) terug bij succes, of (None, error_bericht) bij falen.
    """
    try:
        # Opschonen van eventuele Markdown
        clean_json = raw_content.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)
        
        # Strikte validatie
        profiel = Bedrijfsprofiel(**data)
        return profiel.model_dump(), None
    except json.JSONDecodeError:
        return None, "Ongeldige JSON format"
    except ValidationError as e:
        return None, f"Schema validatie fout: {e.errors()}"

async def run_benchmark(engine_func, test_data: str, iterations: int = 10):
    """Draait een constante test om de accuratesse van het 0.5B model te meten."""
    success_count = 0
    results = []

    print(f"Start benchmark: {iterations} iteraties op Qwen 0.5B...")
    for i in range(iterations):
        raw_output = await engine_func(test_data, raw_mode=True)
        profiel, error = valideer_llm_output(raw_output)
        
        if profiel:
            success_count += 1
            results.append("SUCCESS")
        else:
            results.append(f"FAIL: {error}")
            
    accuratesse = (success_count / iterations) * 100
    print(f"Benchmark klaar. Accuratesse: {accuratesse}%")
    return results