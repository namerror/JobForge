# LLM Skill Selector User Test - 04/11/2026
I requested the LLM-based skill selector using the default model (gpt-5-mini) with the same payload as the embedding test to compare results.
```json
{
  "job_role": "Backend Engineer",
  "technology": [
    "CSS", "Node.JS", "Django", "Figma", "Angular", "Docker", "Kubernetes", "AWS", "Google Cloud", "PyTorch", "Unity", "Unreal Engine", "Pandas", "Matplotlib", "SAP", "Springboot", "TailwindCSS"
  ],
  "programming": [
    "Matlab", "Assembly", "TypeScript", "Java", "C#", "Rust", "python"
  ],
  "concepts": [
    "Rest", "API", "Database Management", "Penetration Testing", "Data Visualization", "Networking", "Caching", "Distributed Computing", "Web Development", "Machine Learning", "Fullstack Development", "authentication", "session management", "rate limiting", "multi-threading", "UI design"
  ]
}
```

## Failed Test
The response body indicates it has failed LLM selection and fell back to baseline
```json
{
    ...,
    "_warnings": [
      "LLM selection failed; fell back to baseline: LLM request failed: Error code: 400 - {'error': {'message': \"Unsupported parameter: 'temperature' is not supported with this model.\", 'type': 'invalid_request_error', 'param': 'temperature', 'code': None}}"
    ],
    "_llm": {
      "fallback": "baseline",
      "reason": "LLM selection failed; fell back to baseline: LLM request failed: Error code: 400 - {'error': {'message': \"Unsupported parameter: 'temperature' is not supported with this model.\", 'type': 'invalid_request_error', 'param': 'temperature', 'code': None}}"
    }
  }
}
```

## 2nd Try
After [fixing](/docs/devlog/04-11-2026-Codex-llm-model-parameter-compatibility.md) this issue. The endpoint returned a successful response as follows:
```json
{
  "technology": [
    "AWS",
    "Django",
    "Docker",
    "Kubernetes",
    "Node.JS"
  ],
  "programming": [
    "Java",
    "python",
    "C#",
    "Rust",
    "TypeScript"
  ],
  "concepts": [
    "API",
    "authentication",
    "Caching",
    "Database Management",
    "Distributed Computing"
  ],
  "details": {
    "technology": {
      "AWS": {
        "score": 3,
        "normalized_skill": "amazon web services"
      },
      "Django": {
        "score": 3,
        "normalized_skill": "django"
      },
      "Docker": {
        "score": 3,
        "normalized_skill": "docker"
      },
      "Kubernetes": {
        "score": 3,
        "normalized_skill": "kubernetes"
      },
      "Node.JS": {
        "score": 3,
        "normalized_skill": "nodejs"
      },
      "Springboot": {
        "score": 3,
        "normalized_skill": "springboot"
      },
      "Google Cloud": {
        "score": 2,
        "normalized_skill": "google cloud platform"
      },
      "Matplotlib": {
        "score": 1,
        "normalized_skill": "matplotlib"
      },
      "Pandas": {
        "score": 1,
        "normalized_skill": "pandas"
      },
      "Angular": {
        "score": 0,
        "normalized_skill": "angular"
      },
      "CSS": {
        "score": 0,
        "normalized_skill": "css"
      },
      "Figma": {
        "score": 0,
        "normalized_skill": "figma"
      },
      "PyTorch": {
        "score": 0,
        "normalized_skill": "pytorch"
      },
      "SAP": {
        "score": 0,
        "normalized_skill": "sap"
      },
      "TailwindCSS": {
        "score": 0,
        "normalized_skill": "tailwind"
      },
      "Unity": {
        "score": 0,
        "normalized_skill": "unity"
      },
      "Unreal Engine": {
        "score": 0,
        "normalized_skill": "unreal engine"
      }
    },
    "programming": {
      "Java": {
        "score": 3,
        "normalized_skill": "java"
      },
      "python": {
        "score": 3,
        "normalized_skill": "python"
      },
      "C#": {
        "score": 2,
        "normalized_skill": "c#"
      },
      "Rust": {
        "score": 2,
        "normalized_skill": "rust"
      },
      "TypeScript": {
        "score": 2,
        "normalized_skill": "typescript"
      },
      "Assembly": {
        "score": 0,
        "normalized_skill": "assembly"
      },
      "Matlab": {
        "score": 0,
        "normalized_skill": "matlab"
      }
    },
    "concepts": {
      "API": {
        "score": 3,
        "normalized_skill": "api"
      },
      "authentication": {
        "score": 3,
        "normalized_skill": "authentication"
      },
      "Caching": {
        "score": 3,
        "normalized_skill": "caching"
      },
      "Database Management": {
        "score": 3,
        "normalized_skill": "database management"
      },
      "Distributed Computing": {
        "score": 3,
        "normalized_skill": "distributed computing"
      },
      "multi-threading": {
        "score": 3,
        "normalized_skill": "multi-threading"
      },
      "rate limiting": {
        "score": 3,
        "normalized_skill": "rate limiting"
      },
      "Rest": {
        "score": 3,
        "normalized_skill": "restful api"
      },
      "session management": {
        "score": 3,
        "normalized_skill": "session management"
      },
      "Web Development": {
        "score": 3,
        "normalized_skill": "web development"
      },
      "Networking": {
        "score": 2,
        "normalized_skill": "networking"
      },
      "Data Visualization": {
        "score": 1,
        "normalized_skill": "data visualization"
      },
      "Fullstack Development": {
        "score": 1,
        "normalized_skill": "fullstack development"
      },
      "Machine Learning": {
        "score": 1,
        "normalized_skill": "machine learning"
      },
      "Penetration Testing": {
        "score": 1,
        "normalized_skill": "penetration testing"
      },
      "UI design": {
        "score": 0,
        "normalized_skill": "ui design"
      }
    },
    "_llm": {
      "model": "gpt-5-mini",
      "api_calls": 1,
      "latency_ms": 15455.95,
      "prompt_tokens": 1454,
      "completion_tokens": 1141,
      "total_tokens": 2595
    }
  }
}
```
It seems to be a reasonable skill selection based on the input, with relevant skills like AWS, Django, Java, Python, API, authentication, etc. scoring highly while less relevant ones score low. The LLM call latency is around 15 seconds which is expected for a more complex reasoning task. Overall, this indicates that the LLM-based skill selector is working as intended after fixing the parameter compatibility issue. Further testing with more job roles and skill sets can help validate its performance and identify any edge cases or areas for improvement.