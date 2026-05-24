.PHONY: install test workouts markdown html all clean

-include .env
export

UNITS ?= metric
FORMAT ?= $(if $(filter imperial,$(UNITS)),letter,a4)
SCHEDULE ?= 1

define check_plan
	@if [ -z "$(PLAN)" ]; then \
		echo "No plan set. Set PLAN in .env or run /paicer:create-plan"; \
		exit 1; \
	fi
	@if [ ! -f "$(PLAN)" ]; then \
		echo "Plan file not found: $(PLAN)"; \
		exit 1; \
	fi
endef

install:
	uv sync

test:
	$(check_plan)
	@echo "Running tests..."
	@uv run pytest -v
	@echo "Validating plan..."
	@uv run paicer render --plan $(PLAN) > /dev/null
	@echo "✅ Plan valid"

workouts:
	$(check_plan)
	@uv run paicer sync $(SCOPE) --plan $(PLAN) $(if $(filter 0,$(SCHEDULE)),--no-schedule)

markdown:
	$(check_plan)
	@mkdir -p output
	@uv run paicer render --plan $(PLAN) > output/training_plan.md
	@echo "Created output/training_plan.md"

html:
	$(check_plan)
	@mkdir -p output
	@uv run paicer render --html --format=$(FORMAT) --plan $(PLAN) > output/training_plan.html
	@echo "Created output/training_plan.html ($(FORMAT))"

all: markdown html

clean:
	trash output/
	trash __pycache__
