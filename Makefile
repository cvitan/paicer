.PHONY: install test workouts markdown html all clean

# Load .env
-include .env
export

# UNITS defaults to metric if not in .env
UNITS ?= metric

# Paper format: derived from UNITS, overridable with FORMAT in .env
FORMAT ?= $(if $(filter imperial,$(UNITS)),letter,a4)

# SCHEDULE flag (set to 0 to skip scheduling)
SCHEDULE ?= 1

# Guard: require PLAN to be set and the file to exist
define check_plan
	@if [ -z "$(PLAN)" ]; then \
		echo "No plan set. Run /paicer:create-plan to create one, or set PLAN in .env"; \
		exit 1; \
	fi
	@if [ ! -f "$(PLAN)" ]; then \
		echo "Plan file not found: $(PLAN)"; \
		echo "Run /paicer:create-plan to create a plan, or check the PLAN path in .env"; \
		exit 1; \
	fi
endef

install:
	uv sync

test:
	$(check_plan)
	@echo "Testing YAML syntax..."
	@uv run python -c "import yaml; yaml.safe_load(open('$(PLAN)'))"
	@echo "✅ YAML valid"
	@echo "Testing Python syntax..."
	@uv run python -m py_compile src/*.py
	@echo "✅ Python valid"
	@echo "Validating plan..."
	@PYTHONPATH=src uv run python -c "import sys; from plan_utils import load_plan, validate_training_days; errors = validate_training_days(load_plan(sys.argv[1])); [print('Error: ' + e) for e in errors]; sys.exit(1) if errors else None" "$(PLAN)"
	@echo "✅ Plan valid"

workouts:
	$(check_plan)
	@uv run python src/generate_workouts.py $(PLAN) $(SCOPE) $(if $(filter 0,$(SCHEDULE)),--no-schedule)

markdown:
	$(check_plan)
	@mkdir -p output
	@uv run python src/render_plan.py $(PLAN) > output/training_plan.md
	@echo "Created output/training_plan.md"

html:
	$(check_plan)
	@mkdir -p output
	@uv run python src/render_plan.py $(PLAN) --html --format=$(FORMAT) > output/training_plan.html
	@echo "Created output/training_plan.html ($(FORMAT))"

all: markdown html

clean:
	trash output/
	trash __pycache__
