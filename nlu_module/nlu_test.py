import sys
from nlu_module import NLUModule


def assert_intent(nlu, transcript, expected_intent, expected_params=None, expected_priority=None):
    result = nlu.parse(transcript)
    if result.intent != expected_intent:
        print(f"FAIL: '{transcript}'")
        print(f"  expected intent: {expected_intent}")
        print(f"  got intent:      {result.intent}")
        return False
    if expected_params is not None:
        for key, value in expected_params.items():
            if result.parameters.get(key) != value:
                print(f"FAIL: '{transcript}'")
                print(f"  expected param {key}={value}")
                print(f"  got param {key}={result.parameters.get(key)}")
                return False
    if expected_priority is not None and result.priority != expected_priority:
        print(f"FAIL: '{transcript}'")
        print(f"  expected priority: {expected_priority}")
        print(f"  got priority:      {result.priority}")
        return False
    print(f"PASS: '{transcript}' -> {result.intent}")
    return True


def main():
    nlu = NLUModule()
    tests = []

    tests.append(assert_intent(nlu, "Move to position A", "motion.move_to", {"target": "a"}, 3))
    tests.append(assert_intent(nlu, "go to position B", "motion.move_to", {"target": "b"}, 3))
    tests.append(assert_intent(nlu, "Go home", "motion.go_home", {}, 3))
    tests.append(assert_intent(nlu, "Return home now", "motion.go_home", {}, 3))
    tests.append(assert_intent(nlu, "Pick the object", "motion.pick", {"object": "object"}, 3))
    tests.append(assert_intent(nlu, "grab the wrench", "motion.pick", {"object": "wrench"}, 3))
    tests.append(assert_intent(nlu, "Place it on the table", "motion.place", {"target": "table"}, 3))
    tests.append(assert_intent(nlu, "drop the part", "motion.place", {"target": "part"}, 3))
    tests.append(assert_intent(nlu, "Rotate the wrist", "motion.rotate", {"axis": "wrist"}, 3))
    tests.append(assert_intent(nlu, "turn the joint", "motion.rotate", {"axis": "joint"}, 3))

    tests.append(assert_intent(nlu, "Stop", "safety.stop", {}, 1))
    tests.append(assert_intent(nlu, "halt", "safety.stop", {}, 1))
    tests.append(assert_intent(nlu, "Emergency stop", "safety.emergency_stop", {}, 1))
    tests.append(assert_intent(nlu, "e-stop", "safety.emergency_stop", {}, 1))
    tests.append(assert_intent(nlu, "stop now", "safety.emergency_stop", {}, 1))
    tests.append(assert_intent(nlu, "Slow down", "safety.slow_down", {}, 2))
    tests.append(assert_intent(nlu, "reduce speed please", "safety.slow_down", {}, 2))
    tests.append(assert_intent(nlu, "Pause", "safety.pause", {}, 2))
    tests.append(assert_intent(nlu, "hold position", "safety.pause", {}, 2))
    tests.append(assert_intent(nlu, "Resume", "safety.resume", {}, 2))
    tests.append(assert_intent(nlu, "continue execution", "safety.resume", {}, 2))

    tests.append(assert_intent(nlu, "Where are you", "query.where_are_you", {}, 4))
    tests.append(assert_intent(nlu, "What is your status", "query.status", {}, 4))
    tests.append(assert_intent(nlu, "are you ok", "query.status", {}, 4))
    tests.append(assert_intent(nlu, "Current position", "query.current_position", {}, 4))
    tests.append(assert_intent(nlu, "report joint angles", "query.current_position", {}, 4))

    tests.append(assert_intent(nlu, "Move to A, actually stop", "safety.stop", {}, 1))
    tests.append(assert_intent(nlu, "pause and then resume", "safety.pause", {}, 2))
    tests.append(assert_intent(nlu, "go home but slow down", "safety.slow_down", {}, 2))

    tests.append(assert_intent(nlu, "Tell me a joke", None, {}, None))
    tests.append(assert_intent(nlu, "what is the weather", None, {}, None))
    tests.append(assert_intent(nlu, "", None, {}, None))
    tests.append(assert_intent(nlu, "   ", None, {}, None))

    passed = sum(1 for t in tests if t)
    total = len(tests)

    print()
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    if passed != total:
        sys.exit(1)


if __name__ == "__main__":
    main()
