import json

from pipeline.core import PipelineResult, write_output


def _result(new_data, changelog_entry):
    return PipelineResult(
        new_data=new_data,
        diff={"added": [], "removed": [], "changed": [], "renamed": []},
        should_commit=True,
        abort_reason=None,
        changelog_entry=changelog_entry,
    )


def test_write_output_appends_to_existing_changelog_rather_than_overwriting(tmp_path):
    data_path = tmp_path / "data.json"
    changelog_path = tmp_path / "changelog.json"

    write_output(_result([{"slug": "a"}], {"date": "run-1", "summary": "1 nouveau projet"}), data_path, changelog_path)
    write_output(_result([{"slug": "a"}, {"slug": "b"}], {"date": "run-2", "summary": "1 nouveau projet"}), data_path, changelog_path)

    changelog = json.loads(changelog_path.read_text(encoding="utf-8"))
    assert [entry["date"] for entry in changelog] == ["run-1", "run-2"]

    data = json.loads(data_path.read_text(encoding="utf-8"))
    assert [record["slug"] for record in data] == ["a", "b"]  # data.json itself is still fully replaced, not appended
