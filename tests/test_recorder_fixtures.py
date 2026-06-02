"""Every supported call recorder must normalize correctly, end to end.

One faithful fixture per recorder (built from each platform's documented export /
API shape), run through ``load_transcript`` so adapter auto-detection, turn merging,
timestamp-unit conversion, and role labeling are all exercised. This is the
regression net behind the "works with any recorder" claim.

Three formats carry roles natively (Gong `affiliation`, Recall `is_host`, plaintext
role labels) and must resolve rep/prospect on their own. The rest have no role field,
so turns/text/timestamps must be perfect but sides come in `unknown` until the user
supplies ``--participants`` (the documented re-stitching tax) — asserted separately.
"""
import json

import pytest

from gtmsi.adapters import load_transcript
from gtmsi.cli import _apply_participants

# Each fixture is the same logical 2-party call. The second turn starts at 9.5s
# (or 9000–9500 ms in the recorder's own unit) so the ms->seconds conversion is
# checked: after normalization turn[1].start_seconds must be ~9, never ~9000.
FIXTURES = {
    # recorder: (filename, content, expected_turns, native_roles)
    "gong": (
        "gong.json",
        {"callTranscripts": [{
            "parties": [
                {"speakerId": "1", "name": "Dana Lee", "affiliation": "Internal"},
                {"speakerId": "2", "name": "Priya Rao", "affiliation": "External"},
            ],
            "transcript": [
                {"speakerId": "1", "sentences": [
                    {"start": 0, "text": "Thanks for the time."},
                    {"start": 3200, "text": "What pushed you to look now?"}]},
                {"speakerId": "2", "sentences": [{"start": 9500, "text": "Renewal is Q3 and reporting is a bottleneck."}]},
                {"speakerId": "1", "sentences": [{"start": 15000, "text": "Who feels that most?"}]},
            ],
        }]},
        3, True,
    ),
    "fireflies": (
        "fireflies.json",
        {"data": {"transcript": {"sentences": [
            {"speaker_name": "Dana Lee", "text": "Thanks for the time. What pushed you to look now?", "start_time": 0.0},
            {"speaker_name": "Priya Rao", "text": "Renewal is Q3 and reporting is a bottleneck.", "start_time": 9.5},
            {"speaker_name": "Dana Lee", "text": "Who feels that most?", "start_time": 15.0},
        ]}}},
        3, False,
    ),
    "otter": (
        "otter.json",
        {"speakers": [{"id": 1, "name": "Dana Lee"}, {"id": 2, "name": "Priya Rao"}],
         "utterances": [
             {"speaker_id": 1, "transcript": "Thanks for the time. What pushed you to look now?", "start_offset": 0},
             {"speaker_id": 2, "transcript": "Renewal is Q3 and reporting is a bottleneck.", "start_offset": 9500},
             {"speaker_id": 1, "transcript": "Who feels that most?", "start_offset": 15000},
         ]},
        3, False,
    ),
    "recall": (
        "recall.json",
        [
            {"participant": {"id": 1, "name": "Dana Lee", "is_host": True},
             "words": [{"text": "Thanks", "start_timestamp": {"relative": 0.0}},
                       {"text": "for the time.", "start_timestamp": {"relative": 0.5}}]},
            {"participant": {"id": 2, "name": "Priya Rao", "is_host": False},
             "words": [{"text": "Renewal is Q3 and reporting is a bottleneck.", "start_timestamp": {"relative": 9.5}}]},
            {"participant": {"id": 1, "name": "Dana Lee", "is_host": True},
             "words": [{"text": "Who feels that most?", "start_timestamp": {"relative": 15.0}}]},
        ],
        3, True,
    ),
    "grain": (
        "grain.json",
        [
            {"start": 0, "end": 3000, "text": "Thanks for the time. What pushed you to look now?", "speaker": "Dana Lee", "participant_id": "a"},
            {"start": 9500, "end": 14000, "text": "Renewal is Q3 and reporting is a bottleneck.", "speaker": "Priya Rao", "participant_id": "b"},
            {"start": 15000, "end": 18000, "text": "Who feels that most?", "speaker": "Dana Lee", "participant_id": "a"},
        ],
        3, False,
    ),
    "vtt": (
        "zoom.vtt",
        "WEBVTT\n\n1\n00:00:00.000 --> 00:00:08.000\nDana Lee: Thanks for the time. What pushed you to look now?\n\n"
        "2\n00:00:09.500 --> 00:00:14.000\nPriya Rao: Renewal is Q3 and reporting is a bottleneck.\n\n"
        "3\n00:00:15.000 --> 00:00:18.000\nDana Lee: Who feels that most?\n",
        3, False,
    ),
    "srt": (
        "call.srt",
        "1\n00:00:00,000 --> 00:00:08,000\nDana Lee: Thanks for the time. What pushed you to look now?\n\n"
        "2\n00:00:09,500 --> 00:00:14,000\nPriya Rao: Renewal is Q3 and reporting is a bottleneck.\n\n"
        "3\n00:00:15,000 --> 00:00:18,000\nDana Lee: Who feels that most?\n",
        3, False,
    ),
    "json-generic": (
        "generic.json",
        {"segments": [
            {"speaker": "Dana Lee", "text": "Thanks for the time. What pushed you to look now?", "start": 0.0},
            {"speaker": "Priya Rao", "text": "Renewal is Q3 and reporting is a bottleneck.", "start": 9.5},
            {"speaker": "Dana Lee", "text": "Who feels that most?", "start": 15.0},
        ]},
        3, False,
    ),
    "plaintext": (
        "call.txt",
        "[00:00] Rep (Dana Lee): Thanks for the time. What pushed you to look now?\n"
        "[00:09] Prospect (Priya Rao): Renewal is Q3 and reporting is a bottleneck.\n"
        "[00:15] Rep (Dana Lee): Who feels that most?\n",
        3, True,
    ),
}


def _write(tmp_path, fn, content):
    p = tmp_path / fn
    p.write_text(content if isinstance(content, str) else json.dumps(content))
    return str(p)


@pytest.mark.parametrize("recorder", list(FIXTURES))
def test_recorder_normalizes_cleanly(tmp_path, recorder):
    fn, content, expected_turns, native_roles = FIXTURES[recorder]
    t = load_transcript(_write(tmp_path, fn, content))

    # Correct adapter auto-detected (json-generic maps to source "json").
    assert t.source["adapter"] == recorder

    # Turns merged to the expected count, every turn has text.
    assert len(t.turns) == expected_turns
    assert all(turn.text.strip() for turn in t.turns)

    # Timestamp present and in SECONDS, not the recorder's raw ms (the conversion bug
    # this guards): the 2nd turn is ~9s, never ~9000.
    t2 = t.turns[1].start_seconds
    assert t2 is not None and 8 <= t2 <= 11, f"{recorder}: bad timestamp unit ({t2})"

    # Formats with a native role/affiliation/host field must resolve rep + prospect.
    sides = {turn.side for turn in t.turns}
    if native_roles:
        assert "rep" in sides and "prospect" in sides, f"{recorder}: roles not resolved ({sides})"


def test_roleless_recorder_resolves_with_participants(tmp_path):
    """A format with no role field comes in `unknown`, and --participants fixes it."""
    fn, content, _, _ = FIXTURES["grain"]
    t = load_transcript(_write(tmp_path, fn, content))
    assert {turn.side for turn in t.turns} == {"unknown"}

    _apply_participants(t, '{"Dana Lee": "rep", "Priya Rao": "prospect"}')
    sides = {turn.side for turn in t.turns}
    assert "rep" in sides and "prospect" in sides


def test_naming_one_side_infers_the_other_in_two_party_call(tmp_path):
    """In a 2-speaker call, naming only the rep infers the other speaker as prospect."""
    fn, content, _, _ = FIXTURES["fireflies"]
    t = load_transcript(_write(tmp_path, fn, content))
    assert {turn.side for turn in t.turns} == {"unknown"}

    _apply_participants(t, '{"Dana Lee": "rep"}')  # only the rep named
    by_speaker = {turn.speaker: turn.side for turn in t.turns}
    assert by_speaker["Dana Lee"] == "rep"
    assert by_speaker["Priya Rao"] == "prospect"  # inferred


def test_no_inference_with_three_speakers(tmp_path):
    """Inference is conservative: 3+ speakers are left alone (name them explicitly)."""
    p = tmp_path / "three.json"
    p.write_text(json.dumps({"segments": [
        {"speaker": "Dana Lee", "text": "Thanks for joining.", "start": 0.0},
        {"speaker": "Priya Rao", "text": "Happy to be here.", "start": 5.0},
        {"speaker": "Sam Okafor", "text": "Me too.", "start": 9.5},
    ]}))
    t = load_transcript(str(p))
    _apply_participants(t, '{"Dana Lee": "rep"}')
    by_speaker = {turn.speaker: turn.side for turn in t.turns}
    assert by_speaker["Dana Lee"] == "rep"
    assert by_speaker["Priya Rao"] == "unknown"  # not guessed
    assert by_speaker["Sam Okafor"] == "unknown"
