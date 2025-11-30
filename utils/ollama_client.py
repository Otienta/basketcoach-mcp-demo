# utils/ollama_client.py
import requests
import logging
import time
from typing import Optional

logger = logging.getLogger("ollama")

def check_ollama_health(base_url: str = "http://localhost:11434") -> bool:
    """Vérifie si Ollama est accessible (endpoint /api/tags)."""
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        return response.status_code == 200
    except Exception:
        return False

def generate_with_ollama(prompt: str, model: str = "llama3.1:8b", max_retries: int = 5, base_url: str = "http://localhost:11434", max_wait_model_ready: int = 600) -> str:
    """
    Génération robuste avec Ollama :
    - attend que le service et le modèle soient disponibles,
    - essaye /api/generate puis /api/chat,
    - backoff exponentiel entre tentatives,
    - gère plusieurs formes de réponse JSON.
    """
    def model_ready() -> bool:
        try:
            resp = requests.get(f"{base_url}/api/tags", timeout=5)
            if resp.status_code != 200:
                return False
            data = resp.json()
            return model in str(data)
        except Exception:
            return False

    # Attente pour disponibilité du modèle (utile au premier démarrage)
    waited = 0
    poll_interval = 5
    while not model_ready() and waited < max_wait_model_ready:
        logger.info(f"Ollama: modèle '{model}' non disponible, attente {waited}s...")
        time.sleep(poll_interval)
        waited += poll_interval

    if not model_ready():
        logger.error(f"Ollama: modèle '{model}' introuvable après {max_wait_model_ready}s.")
        return "[IA locale non prête : modèle indisponible]"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 1024,
            "top_k": 40,
            "top_p": 0.9
        }
    }

    url_candidates = [f"{base_url}/api/generate", f"{base_url}/api/chat"]
    for attempt in range(1, max_retries + 1):
        for url in url_candidates:
            try:
                timeout = 300 if attempt == 1 else 120  # laisser plus de temps au premier appel lourd
                resp = requests.post(url, json=payload, timeout=timeout, headers={"Content-Type": "application/json"})
                # gérer cas de status non-OK
                if resp.status_code in (200, 201):
                    try:
                        result = resp.json()
                    except Exception:
                        return resp.text or "[Réponse non JSON]"
                    # différents formats possibles
                    if isinstance(result, dict):
                        return result.get("response") or result.get("result") or result.get("message", {}).get("content") or result.get("output") or str(result)
                    return str(result)
                elif resp.status_code == 202:
                    logger.info(f"Ollama: génération démarée (202) sur {url}, tentative {attempt}")
                    # courte attente pour génération asynchrone
                    time.sleep(5 * attempt)
                    continue
                else:
                    logger.warning(f"Ollama {url} responded {resp.status_code}: {resp.text[:200]}")
            except requests.exceptions.ReadTimeout as e:
                logger.warning(f"Ollama read timeout on {url} (attempt {attempt}): {e}")
            except Exception as e:
                logger.debug(f"Ollama exception on {url} (attempt {attempt}): {e}")
        # backoff
        sleep_for = min(60, 2 ** attempt)
        logger.warning(f"Ollama tentative {attempt} échouée, backoff {sleep_for}s")
        time.sleep(sleep_for)

    logger.error("Ollama: échec après plusieurs tentatives")
    return "[IA locale non disponible après tentatives]"