"""How each audience wants to be written for: the board's "different tones for different people"."""

from comintern.models.chat import Audience

AUDIENCE_INSTRUCTIONS: dict[Audience | None, str] = {
    Audience.MANAGEMENT: (
        "Write for management: start with the business impact (fines, liability, deadlines), then the two or three "
        "decisions or actions that matter most. No technical detail."
    ),
    Audience.IT: (
        "Write for the IT manager who also owns compliance: concrete technical and organisational measures, in the "
        "order to do them, with what evidence each one produces."
    ),
    Audience.LEGAL: (
        "Write for a legal reader: precise, with the article and section references from the passages, and the "
        "conditions under which an obligation applies."
    ),
    None: "Write for a busy person without legal training: plain words, short sentences, concrete next steps.",
}
