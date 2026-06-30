import unittest

from project_maya import (
    MayaSkillArtifact,
    SkillContractError,
    SkillOrigin,
    validate_skill_artifacts,
    validate_skill_text_is_sanitized,
)


class TestHermesSkillsBoundary(unittest.TestCase):
    def test_approved_skill_artifacts_validate_without_loading_skills(self):
        artifacts = (
            MayaSkillArtifact(
                skill_id="information-management/google-workspace",
                origin=SkillOrigin.MAYA_TRAINED,
                version="1.0.0",
                source_path="skills/google-workspace/SKILL.md",
                capabilities=("google.drive.read", "google.calendar.read"),
            ),
            MayaSkillArtifact(
                skill_id="note-taking/project-notes",
                origin=SkillOrigin.HERMES_DEFAULT,
                version="0.17.0+maya",
                source_path="skills/note-taking/project-notes/SKILL.md",
                capabilities=("notes.read", "notes.write"),
            ),
        )

        validate_skill_artifacts(artifacts)

    def test_skill_artifacts_reject_unportable_source_paths(self):
        artifact = MayaSkillArtifact(
            skill_id="google-workspace",
            origin=SkillOrigin.MAYA_TRAINED,
            version="1.0.0",
            source_path="/opt/hermes/skills/google-workspace/SKILL.md",
            capabilities=("google.drive.read",),
        )

        with self.assertRaisesRegex(SkillContractError, "relative and portable"):
            validate_skill_artifacts((artifact,))

    def test_skill_artifacts_reject_missing_capabilities(self):
        artifact = MayaSkillArtifact(
            skill_id="google-workspace",
            origin=SkillOrigin.MAYA_TRAINED,
            version="1.0.0",
            source_path="skills/google-workspace/SKILL.md",
            capabilities=(),
        )

        with self.assertRaisesRegex(SkillContractError, "capabilities"):
            validate_skill_artifacts((artifact,))

    def test_skill_artifacts_reject_duplicates(self):
        artifact = MayaSkillArtifact(
            skill_id="google-workspace",
            origin=SkillOrigin.MAYA_TRAINED,
            version="1.0.0",
            source_path="skills/google-workspace/SKILL.md",
            capabilities=("google.drive.read",),
        )

        with self.assertRaisesRegex(SkillContractError, "duplicate"):
            validate_skill_artifacts((artifact, artifact))

    def test_skill_text_sanitization_rejects_personal_and_secret_markers(self):
        unsafe_text = "Use tseretelibidzina@gmail.com and oauth_token here."

        with self.assertRaisesRegex(SkillContractError, "personal"):
            validate_skill_text_is_sanitized(unsafe_text)


if __name__ == "__main__":
    unittest.main()
