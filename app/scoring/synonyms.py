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

# From generated json file
SYNONYM_TO_NORMALIZED = {
    "node.js": "nodejs",
    "node": "nodejs",
    "reactjs": "react",
    "react.js": "react",
    "vuejs": "vue",
    "vue.js": "vue",
    "angularjs": "angular",
    "angular.js": "angular",
    "bootstrapcss": "bootstrap",
    "bootstrap css": "bootstrap",
    "tailwindcss": "tailwind",
    "tailwind css": "tailwind",
    "amazon web services": "aws",
    "amazon cloud": "aws",
    "microsoft azure": "azure",
    "azure cloud": "azure",
    "google cloud platform": "gcp",
    "google cloud": "gcp",
    "continuous integration": "ci/cd",
    "continuous delivery": "ci/cd",
    "continuous deployment": "ci/cd",
    "ci": "ci/cd",
    "cd": "ci/cd",
    "cicd": "ci/cd",
    "cicd pipelines": "ci/cd",
    "reactnative": "react native",
    "react-native": "react native",
    "postgres": "postgresql",
    "js": "javascript",
    "csharp": "c#",
    "recurrent neural network": "rnn",
    "convolutional neural network": "cnn",
    "natural language processing": "nlp",
    "generative ai": "genai",
    "generative artificial intelligence": "genai",
    "randomforest": "random forest",
    "random-forest": "random forest",
    "random forest classifier": "random forest",
    "random forests": "random forest"
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
