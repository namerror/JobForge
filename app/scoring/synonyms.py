import json
from pathlib import Path

# mapping synonyms so they can be normalized to a single term for better matching
NORMALIZATION_MAP = {
    "nodejs": ["node.js", "node"],
    "react": ["reactjs", "react.js"],
    "vue": ["vuejs", "vue.js"],
    "angular": ["angularjs", "angular.js"],
    "bootstrap": ["bootstrapcss", "bootstrap css"],
    "tailwind": ["tailwindcss", "tailwind css"],
    "aws": ["amazon web services", "amazon cloud"],
    "azure": ["microsoft azure", "azure cloud"],
    "gcp": ["google cloud platform", "google cloud"],
    "ci/cd": ["continuous integration", "continuous delivery", "continuous deployment", "ci", "cd", "cicd", "cicd pipelines"],
    "react native": ["reactnative", "react-native"],
    "postgresql": ["postgres"],
    "javascript": ["js"],
    "c#": ["csharp"],
    "rnn": ["recurrent neural network"],
    "cnn": ["convolutional neural network"],
    "nlp": ["natural language processing"],
    "machine learning": ["ml"],
    "genai": ["generative ai", "generative artificial intelligence"],
    "random forest": ["randomforest", "random-forest", "random forest classifier", "random forests"],
    "api": ["apis"],
    "oop": ["object-oriented programming", "object oriented programming"],
}


def _load_synonyms() -> dict:
    data_path = Path(__file__).parent.parent / "data" / "synonym_to_normalized.json"
    with open(data_path) as f:
        return json.load(f)


SYNONYM_TO_NORMALIZED = _load_synonyms()


if __name__ == "__main__":
    # reverse the normalization map to create a mapping from synonyms to their normalized form
    result = {}
    for normalized, synonyms in NORMALIZATION_MAP.items():
        for synonym in synonyms:
            result[synonym] = normalized

    # store the reversed mapping
    out_path = Path(__file__).parent.parent / "data" / "synonym_to_normalized.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=4)
