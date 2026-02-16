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
    "genai": ["generative ai", "generative artificial intelligence"],
    "random forest": ["randomforest", "random-forest", "random forest classifier", "random forests"],
}

if __name__ == "__main__":
    import os

    file_dir = os.path.dirname(__file__)

    # reverse the normalization map to create a mapping from synonyms to their normalized form
    SYNONYM_TO_NORMALIZED = {}
    for normalized, synonyms in NORMALIZATION_MAP.items():
        for synonym in synonyms:
            SYNONYM_TO_NORMALIZED[synonym] = normalized
    
    # store the reversed mapping
    with open(os.path.join(file_dir, "synonym_to_normalized.json"), "w") as f:
        import json
        json.dump(SYNONYM_TO_NORMALIZED, f, indent=4)
