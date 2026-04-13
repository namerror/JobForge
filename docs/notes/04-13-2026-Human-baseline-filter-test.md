# Baseline Filter Test
We are testing the baseline filter today to ensure a baseline selection is made before the LLM selection. This is important for token efficiency and better performance. 
This is the payload we used:
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
  ],
  "baseline_filter": true
}
```

## Results
The response body:
```json
{
  "technology": [
    "AWS",
    "Django",
    "Docker",
    "Google Cloud",
    "Kubernetes"
  ],
  "programming": [
    "C#",
    "Java",
    "python",
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
        "source": "llm",
        "normalized_skill": "amazon web services",
        "method_score": 3,
        "normalized_final_score": 1
      },
      "Django": {
        "source": "baseline",
        "baseline_score": 3,
        "normalized_skill": "django",
        "normalized_final_score": 1
      },
      "Docker": {
        "source": "baseline",
        "baseline_score": 3,
        "normalized_skill": "docker",
        "normalized_final_score": 1
      },
      "Google Cloud": {
        "source": "llm",
        "normalized_skill": "google cloud platform",
        "method_score": 3,
        "normalized_final_score": 1
      },
      "Kubernetes": {
        "source": "baseline",
        "baseline_score": 3,
        "normalized_skill": "kubernetes",
        "normalized_final_score": 1
      },
      "Node.JS": {
        "source": "llm",
        "normalized_skill": "nodejs",
        "method_score": 3,
        "normalized_final_score": 1
      },
      "Springboot": {
        "source": "llm",
        "normalized_skill": "springboot",
        "method_score": 3,
        "normalized_final_score": 1
      },
      "Angular": {
        "source": "llm",
        "normalized_skill": "angular",
        "method_score": 0,
        "normalized_final_score": 0
      },
      "CSS": {
        "source": "llm",
        "normalized_skill": "css",
        "method_score": 0,
        "normalized_final_score": 0
      },
      "Figma": {
        "source": "llm",
        "normalized_skill": "figma",
        "method_score": 0,
        "normalized_final_score": 0
      },
      "Matplotlib": {
        "source": "llm",
        "normalized_skill": "matplotlib",
        "method_score": 0,
        "normalized_final_score": 0
      },
      "Pandas": {
        "source": "llm",
        "normalized_skill": "pandas",
        "method_score": 0,
        "normalized_final_score": 0
      },
      "PyTorch": {
        "source": "llm",
        "normalized_skill": "pytorch",
        "method_score": 0,
        "normalized_final_score": 0
      },
      "SAP": {
        "source": "llm",
        "normalized_skill": "sap",
        "method_score": 0,
        "normalized_final_score": 0
      },
      "TailwindCSS": {
        "source": "llm",
        "normalized_skill": "tailwind",
        "method_score": 0,
        "normalized_final_score": 0
      },
      "Unity": {
        "source": "llm",
        "normalized_skill": "unity",
        "method_score": 0,
        "normalized_final_score": 0
      },
      "Unreal Engine": {
        "source": "llm",
        "normalized_skill": "unreal engine",
        "method_score": 0,
        "normalized_final_score": 0
      }
    },
    "programming": {
      "C#": {
        "source": "baseline",
        "baseline_score": 3,
        "normalized_skill": "c#",
        "normalized_final_score": 1
      },
      "Java": {
        "source": "baseline",
        "baseline_score": 3,
        "normalized_skill": "java",
        "normalized_final_score": 1
      },
      "python": {
        "source": "baseline",
        "baseline_score": 3,
        "normalized_skill": "python",
        "normalized_final_score": 1
      },
      "Rust": {
        "source": "llm",
        "normalized_skill": "rust",
        "method_score": 2,
        "normalized_final_score": 0.6666666666666666
      },
      "TypeScript": {
        "source": "llm",
        "normalized_skill": "typescript",
        "method_score": 2,
        "normalized_final_score": 0.6666666666666666
      },
      "Assembly": {
        "source": "llm",
        "normalized_skill": "assembly",
        "method_score": 0,
        "normalized_final_score": 0
      },
      "Matlab": {
        "source": "llm",
        "normalized_skill": "matlab",
        "method_score": 0,
        "normalized_final_score": 0
      }
    },
    "concepts": {
      "API": {
        "source": "baseline",
        "baseline_score": 3,
        "normalized_skill": "api",
        "normalized_final_score": 1
      },
      "authentication": {
        "source": "baseline",
        "baseline_score": 3,
        "normalized_skill": "authentication",
        "normalized_final_score": 1
      },
      "Caching": {
        "source": "llm",
        "normalized_skill": "caching",
        "method_score": 3,
        "normalized_final_score": 1
      },
      "Database Management": {
        "source": "llm",
        "normalized_skill": "database management",
        "method_score": 3,
        "normalized_final_score": 1
      },
      "Distributed Computing": {
        "source": "llm",
        "normalized_skill": "distributed computing",
        "method_score": 3,
        "normalized_final_score": 1
      },
      "multi-threading": {
        "source": "llm",
        "normalized_skill": "multi-threading",
        "method_score": 3,
        "normalized_final_score": 1
      },
      "rate limiting": {
        "source": "llm",
        "normalized_skill": "rate limiting",
        "method_score": 3,
        "normalized_final_score": 1
      },
      "Rest": {
        "source": "llm",
        "normalized_skill": "restful api",
        "method_score": 3,
        "normalized_final_score": 1
      },
      "session management": {
        "source": "llm",
        "normalized_skill": "session management",
        "method_score": 3,
        "normalized_final_score": 1
      },
      "Web Development": {
        "source": "llm",
        "normalized_skill": "web development",
        "method_score": 3,
        "normalized_final_score": 1
      },
      "Fullstack Development": {
        "source": "llm",
        "normalized_skill": "fullstack development",
        "method_score": 2,
        "normalized_final_score": 0.6666666666666666
      },
      "Networking": {
        "source": "llm",
        "normalized_skill": "networking",
        "method_score": 2,
        "normalized_final_score": 0.6666666666666666
      },
      "Machine Learning": {
        "source": "llm",
        "normalized_skill": "machine learning",
        "method_score": 1,
        "normalized_final_score": 0.3333333333333333
      },
      "Penetration Testing": {
        "source": "llm",
        "normalized_skill": "penetration testing",
        "method_score": 1,
        "normalized_final_score": 0.3333333333333333
      },
      "Data Visualization": {
        "source": "llm",
        "normalized_skill": "data visualization",
        "method_score": 0,
        "normalized_final_score": 0
      },
      "UI design": {
        "source": "llm",
        "normalized_skill": "ui design",
        "method_score": 0,
        "normalized_final_score": 0
      }
    },
    "_baseline_filter": {
      "enabled": true,
      "requested_method": "llm",
      "fallback": false,
      "categories": {
        "technology": {
          "recognized": 3,
          "unrecognized": 14,
          "second_pass_scored": 14
        },
        "programming": {
          "recognized": 3,
          "unrecognized": 4,
          "second_pass_scored": 4
        },
        "concepts": {
          "recognized": 2,
          "unrecognized": 14,
          "second_pass_scored": 14
        }
      }
    },
    "_llm": {
      "model": "gpt-5-mini",
      "api_calls": 1,
      "latency_ms": 14350.779,
      "prompt_tokens": 1200,
      "completion_tokens": 1133,
      "total_tokens": 2333
    }
  }
}
```
The returned skills seem reasonable. It seems that with baseline filtering enabled, we also manage to lower the token usage. 

However, I'm trying to figure out why a lot of the skills that should be recognized by baseline filter are still passed on to LLM method. For example, "AWS", "Kubernetes" these are all already defined in the baseline filter, so they should not be passed to LLM method at all. We need to investigate this further.

For reference, the baseline filter should look through the role profiles for certain roles, in this case, "Backend Engineer", and pick out the relevant skills that are defined in the baseline filter for that role. 
