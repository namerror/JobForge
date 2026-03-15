# Embedding Skill Selector User Test - 03/15/2026
I have tested the skill selector with embedding method by running the FastAPI app and sending requests to the `/select_skills` endpoint with the following payload:

```
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

to test the embedding-based skill selector. 

## Method 
This is embedding method, to clarify some points about the current implementation to avoid future confusion:
- The skill selector uses OpenAI's embedding API to compute embeddings for the job role and each skill in the request.
- It then calculates cosine similarity between the role embedding and ranks skills purely based on this similarity score.
- The top 5 skills per category are returned in the response, along with their similarity scores and normalized skill names for debugging purposes.

## Results
Response from the embedding-based skill selector:

```json
{
  "technology": [
    "Node.JS",
    "Kubernetes",
    "Unreal Engine",
    "Docker",
    "AWS"
  ],
  "programming": [
    "TypeScript",
    "Java",
    "C#",
    "Matlab",
    "Assembly"
  ],
  "concepts": [
    "Fullstack Development",
    "Web Development",
    "Database Management",
    "Rest",
    "API"
  ],
  "details": {
    "technology": {
      "Node.JS": {
        "similarity": 0.455142,
        "normalized_skill": "nodejs"
      },
      "Kubernetes": {
        "similarity": 0.431675,
        "normalized_skill": "kubernetes"
      },
      "Unreal Engine": {
        "similarity": 0.398889,
        "normalized_skill": "unreal engine"
      },
      "Docker": {
        "similarity": 0.365333,
        "normalized_skill": "docker"
      },
      "AWS": {
        "similarity": 0.360984,
        "normalized_skill": "amazon web services"
      },
      "Django": {
        "similarity": 0.35906,
        "normalized_skill": "django"
      },
      "Springboot": {
        "similarity": 0.352019,
        "normalized_skill": "springboot"
      },
      "Google Cloud": {
        "similarity": 0.345755,
        "normalized_skill": "google cloud platform"
      },
      "Angular": {
        "similarity": 0.310742,
        "normalized_skill": "angular"
      },
      "Matplotlib": {
        "similarity": 0.270224,
        "normalized_skill": "matplotlib"
      },
      "CSS": {
        "similarity": 0.260589,
        "normalized_skill": "css"
      },
      "SAP": {
        "similarity": 0.253199,
        "normalized_skill": "sap"
      },
      "TailwindCSS": {
        "similarity": 0.251698,
        "normalized_skill": "tailwind"
      },
      "Figma": {
        "similarity": 0.251423,
        "normalized_skill": "figma"
      },
      "Unity": {
        "similarity": 0.182473,
        "normalized_skill": "unity"
      },
      "PyTorch": {
        "similarity": 0.173466,
        "normalized_skill": "pytorch"
      },
      "Pandas": {
        "similarity": 0.148413,
        "normalized_skill": "pandas"
      }
    },
    "programming": {
      "TypeScript": {
        "similarity": 0.368364,
        "normalized_skill": "typescript"
      },
      "Java": {
        "similarity": 0.312198,
        "normalized_skill": "java"
      },
      "C#": {
        "similarity": 0.294103,
        "normalized_skill": "c#"
      },
      "Matlab": {
        "similarity": 0.293767,
        "normalized_skill": "matlab"
      },
      "Assembly": {
        "similarity": 0.276582,
        "normalized_skill": "assembly"
      },
      "python": {
        "similarity": 0.247249,
        "normalized_skill": "python"
      },
      "Rust": {
        "similarity": 0.225509,
        "normalized_skill": "rust"
      }
    },
    "concepts": {
      "Fullstack Development": {
        "similarity": 0.531812,
        "normalized_skill": "fullstack development"
      },
      "Web Development": {
        "similarity": 0.459007,
        "normalized_skill": "web development"
      },
      "Database Management": {
        "similarity": 0.373992,
        "normalized_skill": "database management"
      },
      "Rest": {
        "similarity": 0.369149,
        "normalized_skill": "restful api"
      },
      "API": {
        "similarity": 0.367039,
        "normalized_skill": "api"
      },
      "Penetration Testing": {
        "similarity": 0.35776,
        "normalized_skill": "penetration testing"
      },
      "Networking": {
        "similarity": 0.347509,
        "normalized_skill": "networking"
      },
      "UI design": {
        "similarity": 0.329794,
        "normalized_skill": "ui design"
      },
      "Distributed Computing": {
        "similarity": 0.319547,
        "normalized_skill": "distributed computing"
      },
      "authentication": {
        "similarity": 0.311209,
        "normalized_skill": "authentication"
      },
      "Caching": {
        "similarity": 0.298324,
        "normalized_skill": "caching"
      },
      "multi-threading": {
        "similarity": 0.296579,
        "normalized_skill": "multi-threading"
      },
      "session management": {
        "similarity": 0.288698,
        "normalized_skill": "session management"
      },
      "Machine Learning": {
        "similarity": 0.276523,
        "normalized_skill": "machine learning"
      },
      "rate limiting": {
        "similarity": 0.245434,
        "normalized_skill": "rate limiting"
      },
      "Data Visualization": {
        "similarity": 0.221541,
        "normalized_skill": "data visualization"
      }
    }
  }
}
```

## Takeaways
- This test shows the skill selector cannot fully rely on embedding similarity for perfect skill selection. Examples of false positives: "Unreal Engine", "Matlab"; false negatives: "Django", "python". 
- Ranking is not well aligned with relevance, especially for programming languages. Embeddings capture some semantic relationships but miss critical domain-specific signals that the baseline method can catch with keyword matching and boosts.
- The selector does well surfacing relevant concepts, also most technology skills are reasonably ranked.
- This highlights the importance of combining embedding-based similarity with other heuristics and domain knowledge for more accurate skill selection.
- Ranking shouldn't be based on similarity alone, one approach could be to set relevance score based on similarity thresholds and then apply additional rules or boosts to determine final ranking.
- A hybrid method that uses embeddings for initial relevance scoring but also incorporates keyword matching, role-specific boosts, and other heuristics could potentially provide better performance.