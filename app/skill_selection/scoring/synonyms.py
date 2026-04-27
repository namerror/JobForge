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
    "amazon web services": ["aws", "amazon cloud"],
    "azure": ["microsoft azure", "azure cloud"],
    "google cloud platform": ["gcp", "google cloud"],
    "ci/cd": ["continuous integration", "continuous delivery", "continuous deployment", "ci", "cd", "cicd", "cicd pipelines"],
    "react native": ["reactnative", "react-native"],
    "postgresql": ["postgres"],
    "javascript": ["js"],
    "c#": ["csharp"],
    "recurrent neural network": ["rnn"],
    "convolutional neural network": ["cnn"],
    "natural language processing": ["nlp"],
    "machine learning": ["ml"],
    "generative ai": ["genai", "generative artificial intelligence"],
    "random forest": ["randomforest", "random-forest", "random forest classifier", "random forests"],
    "api": ["apis", "application programming interface"],
    "object-oriented programming": ["oop", "object oriented programming"],
    "apache kafka": ["kafka", "apache kafka streaming"],
    "restful api": ["rest api", "restful apis", "restful", "rest"],
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
