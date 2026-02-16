# Mapping of role profiles to their associated keywords and boost terms.

ROLE_PROFILES = {
    "backend": {
        "concepts": {
            "keywords": ["database", "server", "api", "microservices", "cloud", "authentication", "authorization"], 
        },
        "technology": {
            "keywords": ["node.js", "django", "spring", "fastapi", "postgresql", "mysql", "mongodb", "redis", "docker", "kubernetes", "kafka", "aws"]
        },
        "programming": {
            "keywords": ["java", "python", "c#"]
        },
    },
    "frontend": {
        "concepts": {
            "keywords": ["ui", "ux", "accessibility", "responsive", "web", "design", "components", "state"],
        },
        "technology": {
            "keywords": ["react", "vue", "angular", "bootstrap", "tailwind"],
        },
        "programming": {
            "keywords": ["javascript", "typescript", "css", "html"],
        },
    },
    "fullstack": {
        "inherits": ["backend", "frontend", "devops"],
        "concepts": {
            "keywords": [],
        },
        "technology": {
            "keywords": [],
        },
        "programming": {
            "keywords": [],
        },
    },
    "data": {
        "concepts": {
            "keywords": ["nosql", "bi tools", "analysis", "cluster", "cloud", "visualization", "statistics", "big data"],
        },
        "technology": {
            "keywords": ["aws", "matplotlib", "tensorflow", "spark", "hadoop"],
        },
        "programming": {
            "keywords": ["r", "python", "sql"],
        },
    },
    "devops": {
        "concepts": {
            "keywords": ["system", "infrastructure", "automation", "ci/cd", "monitoring", "cloud", "containerization", "orchestration", "networking", "scripting"],
        },
        "technology": {
            "keywords": ["linux", "aws", "azure", "docker", "kubernetes", "ansible", "terraform", "jenkins", "prometheus", "grafana", "google cloud"],
        },
        "programming": {
            "keywords": ["python", "bash", "powershell", "rust", "go", "c", "c++"],
        },
    },
    "security": {
        "concepts": {
            "keywords": ["networking", "cryptography", "system", "encryption", "cybersecurity", "vulnerability", "penetration testing", "compliance", "firewall", "intrusion detection", "incident response", "reverse engineering", "fuzzing", "malware analysis"],
        },
        "technology": {
            "keywords": ["linux", "windows", "aws", "azure", "gcp", "metasploit", "nmap", "wireshark", "burp suite"],
        },
        "programming": {
            "keywords": ["rust", "c", "assembly", "python", "c++", "bash"],
        },
    },
    "mobile": {
        "concepts": {
            "keywords": ["mobile", "app", "android", "ios"],
        },
        "technology": {
            "keywords": ["react native", "flutter"],
        },
        "programming": {
            "keywords": ["swift", "kotlin", "java", "javascript"],
        },
    },
    "ml/ai": {
        "concepts": {
            "keywords": ["machine learning", "deep learning", "neural networks", "data science", "artificial intelligence", "rnn", "cnn", "nlp", "computer vision", "reinforcement learning", "genai", "random forest", "decision tree"],
        },
        "technology": {
            "keywords": ["tensorflow", "pytorch", "scikit-learn", "pandas", "numpy"],
        },
        "programming": {
            "keywords": ["python", "c++"],
        },
    }
}