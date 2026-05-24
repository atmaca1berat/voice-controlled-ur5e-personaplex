.PHONY: build clean test

build:
	colcon build --packages-select personaplex_bridge voice_task_executor

clean:
	rm -rf build install log

test:
	cd nlu_module && python3 nlu_test.py
