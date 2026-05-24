import re
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional


@dataclass
class IntentSpec:
    intent_id: str
    priority: int
    keywords: List[str]
    parameter_extractors: Dict[str, str] = field(default_factory=dict)


INTENTS: List[IntentSpec] = [
    IntentSpec(
        intent_id="safety.emergency_stop",
        priority=1,
        keywords=["emergency stop", "e-stop", "stop now", "stop immediately"],
    ),
    IntentSpec(
        intent_id="safety.stop",
        priority=1,
        keywords=["stop", "halt"],
    ),
    IntentSpec(
        intent_id="safety.pause",
        priority=2,
        keywords=["pause", "hold"],
    ),
    IntentSpec(
        intent_id="safety.slow_down",
        priority=2,
        keywords=["slow down", "reduce speed"],
    ),
    IntentSpec(
        intent_id="safety.resume",
        priority=2,
        keywords=["resume", "continue"],
    ),
    IntentSpec(
        intent_id="motion.go_home",
        priority=3,
        keywords=["go home", "return home", "home position"],
    ),
    IntentSpec(
        intent_id="motion.move_to",
        priority=3,
        keywords=["move to", "go to"],
        parameter_extractors={"target": r"(?:move|go) to (?:position )?([a-z0-9]+)"},
    ),
    IntentSpec(
        intent_id="motion.pick",
        priority=3,
        keywords=["pick", "grab", "take"],
        parameter_extractors={"object": r"(?:pick|grab|take) (?:up |the )?([a-z]+)"},
    ),
    IntentSpec(
        intent_id="motion.place",
        priority=3,
        keywords=["place", "put", "drop"],
        parameter_extractors={"target": r"(?:place|put|drop) (?:it )?(?:on |at )?(?:the )?([a-z]+)"},
    ),
    IntentSpec(
        intent_id="motion.rotate",
        priority=3,
        keywords=["rotate", "turn", "spin"],
        parameter_extractors={"axis": r"(?:rotate|turn|spin)(?: the)? ([a-z]+)"},
    ),
    IntentSpec(
        intent_id="query.where_are_you",
        priority=4,
        keywords=["where are you"],
    ),
    IntentSpec(
        intent_id="query.status",
        priority=4,
        keywords=["what is your status", "status", "are you ok"],
    ),
    IntentSpec(
        intent_id="query.current_position",
        priority=4,
        keywords=["current position", "joint angles", "position"],
    ),
]


@dataclass
class NLUResult:
    intent: Optional[str]
    parameters: Dict[str, str]
    priority: Optional[int]
    raw_transcript: str
    matched_keywords: List[str]
    confidence: str

    def to_dict(self) -> Dict:
        return asdict(self)


class NLUModule:
    def __init__(self, intent_specs: List[IntentSpec] = None):
        self.intents = intent_specs if intent_specs is not None else INTENTS

    def normalize(self, transcript: str) -> str:
        text = transcript.lower().strip()
        text = re.sub(r"[.!?,;:]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def find_matches(self, normalized: str) -> List[tuple]:
        matches = []
        for spec in self.intents:
            for keyword in spec.keywords:
                if keyword in normalized:
                    matches.append((spec, keyword))
                    break
        return matches

    def extract_parameters(self, spec: IntentSpec, normalized: str) -> Dict[str, str]:
        params = {}
        for param_name, pattern in spec.parameter_extractors.items():
            match = re.search(pattern, normalized)
            if match:
                params[param_name] = match.group(1)
        return params

    def parse(self, transcript: str) -> NLUResult:
        if not transcript or not transcript.strip():
            return NLUResult(
                intent=None,
                parameters={},
                priority=None,
                raw_transcript=transcript,
                matched_keywords=[],
                confidence="unknown",
            )

        normalized = self.normalize(transcript)
        matches = self.find_matches(normalized)

        if not matches:
            return NLUResult(
                intent=None,
                parameters={},
                priority=None,
                raw_transcript=transcript,
                matched_keywords=[],
                confidence="unknown",
            )

        matches.sort(key=lambda m: m[0].priority)
        winner_spec, winner_keyword = matches[0]
        all_matched_keywords = [kw for _, kw in matches]

        params = self.extract_parameters(winner_spec, normalized)

        return NLUResult(
            intent=winner_spec.intent_id,
            parameters=params,
            priority=winner_spec.priority,
            raw_transcript=transcript,
            matched_keywords=all_matched_keywords,
            confidence="exact_match",
        )


if __name__ == "__main__":
    nlu = NLUModule()
    examples = [
        "Move to position A",
        "Go home",
        "Pick the object",
        "Place it on the table",
        "Rotate the wrist",
        "Stop",
        "Emergency stop",
        "Slow down",
        "Pause",
        "Resume",
        "Where are you",
        "What is your status",
        "Current position",
        "Move to A actually stop",
        "Tell me a joke",
    ]
    for transcript in examples:
        result = nlu.parse(transcript)
        print(f"Input:  {transcript}")
        print(f"Intent: {result.intent}")
        print(f"Params: {result.parameters}")
        print(f"Conf:   {result.confidence}")
        print(f"Match:  {result.matched_keywords}")
        print("-" * 60)
