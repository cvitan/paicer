.PHONY: install test workouts markdown html review-data all clean

# Load .env (required for PLAN)
-include .env
export

# PLAN must be set in .env or command line
ifndef PLAN
$(error PLAN not set. Set in .env or use: make <target> PLAN=plans/your-plan.yaml)
endif

# FORMAT defaults to letter if not in .env
FORMAT ?= letter

# SCHEDULE flag (set to 0 to skip scheduling)
SCHEDULE ?= 1

install:
	uv sync

test:
	@echo "Testing YAML syntax..."
	@uv run python -c "import yaml; yaml.safe_load(open('$(PLAN)'))"
	@echo "✅ YAML valid"
	@echo "Testing Python syntax..."
	@uv run python -m py_compile src/*.py
	@echo "✅ Python valid"

workouts:
	@uv run python src/generate_workouts.py $(PLAN) $(SCOPE) $(if $(filter 0,$(SCHEDULE)),--no-schedule)

markdown:
	@mkdir -p output
	@uv run python src/render_plan.py $(PLAN) > output/training_plan.md
	@echo "Created output/training_plan.md"

html:
	@mkdir -p output
	@uv run python src/render_plan.py $(PLAN) --html --format=$(FORMAT) > output/training_plan.html
	@echo "Created output/training_plan.html ($(FORMAT))"

review-data:
	@uv run python src/review_data.py $(PLAN) $(SCOPE)

all: markdown html

clean:
	trash output/
	trash __pycache__
