# entry point for resume generation

from resume_evidence import load_registered_evidence
from resume_generation.selection import generate_selection_context


def bullet_point_generation(loaded_evidence, project_ids):
    pass


if __name__ == "__main__":
    loaded_evidence = load_registered_evidence()
    context = generate_selection_context(loaded_evidence=loaded_evidence)
    job_target = context.job_target

    # TODO: load basic user info (name, contact info, etc)

    # TODO: other info like experience, publications etc. will come in the future

    # selection: skills and projects, both ranked by relevance to the job target.
    project_ids = context.project_selection.selected_project_ids
    skills = context.selected_skills

    # TODO: optionally re-rank project skills with LLM (not the skills themselves), this is ranked per project, priortizing skills that are more relevant to the job target. This should be done with a separate reranking API instead of the one used for regular skill ranking

    # TODO: bullet point generation. Call the "/generate-bulletpoints" API with the project records
    bullet_point_generation(loaded_evidence=loaded_evidence, project_ids=project_ids)

    # TODO: optionally overall content validation

    # TODO: generation step, using the results to generate a working resume draft schema, this will be used to generate the actual resume content in the future

    # TODO: output LaTeX format resume, this is the final output for now, but in the future we can also output other formats like PDF, Word, etc.
