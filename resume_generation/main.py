# entry point for resume generation

from resume_generation.selection import (generate_selection_context)

if __name__ == "__main__":

    # TODO: load basic user info (name, contact info, etc)

    # TODO: other info like experience, publications etc. will come in the future

    # selection: skills and projects
    context = generate_selection_context()
    ranked_projects = context.project_selection.ranked_projects
    skills = context.selected_skills # already ranked

    # TODO: optionally re-rank project skills (not the skills themselves), this is ranked per project, priortizing skills that are more relevant to the job target

    # TODO: Refinement: project highlight refinement, this is to be implemented

    # TODO: optionally overall content validation

    # TODO: generation step, using the results to generate a working resume draft schema, this will be used to generate the actual resume content in the future

    # TODO: output LaTeX format resume, this is the final output for now, but in the future we can also output other formats like PDF, Word, etc.