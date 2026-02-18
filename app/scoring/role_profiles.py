# Mapping of role profiles to their associated keywords and boost terms.
ROLE_PROFILES = {
    "general": {
        "inherits": ["fullstack", "ml/ai"],
        "concepts": {
            "keywords": ["software", "programming", "architecture","testing", "debugging","agile", "scrum", "oop"],
        },
        "technology": {
            "keywords": ["git", "rest", "docker", "kubernetes", "aws", "azure", "gcp", "linux"],
        },
        "programming": {
            "keywords": ["python", "java", "javascript", "c#", "c++", "c", "sql", "rust"],
        }
    },
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
            "keywords": ["linux", "aws", "azure", "docker", "kubernetes", "ansible", "terraform", "jenkins", "prometheus", "grafana", "gcp"],
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

def detect_role_family(job_role: str) -> str:
    job_role_clean = job_role.lower().strip()
    tokens = job_role_clean.replace("-", " ").split()

    # Most specific first
    if "mobile" in tokens:
        return "mobile"
    if "fullstack" in tokens or ("full" in tokens and "stack" in tokens):
        return "fullstack"
    if "backend" in tokens:
        return "backend"
    if "frontend" in tokens:
        return "frontend"
    if "devops" in tokens:
        return "devops"
    if "ml" in tokens or "machine" in tokens and "learning" in tokens or "ai" in tokens:
        return "ml"
    if "data" in tokens:
        return "data"
    if "security" in tokens or "cybersecurity" in tokens:
        return "security"

    return "general"