# Makefile for Data Platform Testing

.PHONY: help install-test-deps test-smoke test-generation test-scalability test-performance test-database test-xs test-full test-deps clean

# Default target
help:
	@echo "Data Platform Test Suite Commands"
	@echo "================================="
	@echo ""
	@echo "Setup:"
	@echo "  install-test-deps  Install test dependencies"
	@echo "  test-deps         Check dependencies"
	@echo ""
	@echo "Quick Tests:"
	@echo "  test-smoke        Run smoke tests (5-10 min)"
	@echo "  test-xs           Test XS generation end-to-end (5-10 min)"
	@echo ""
	@echo "Comprehensive Tests:"
	@echo "  test-generation   Test all data generators (10-15 min)"
	@echo "  test-scalability  Test scaling behavior (15-20 min)" 
	@echo "  test-performance  Test performance benchmarks (10-15 min)"
	@echo "  test-database     Test database integration (5-10 min)"
	@echo ""
	@echo "Full Suite:"
	@echo "  test-full         Run complete test suite (30-45 min)"
	@echo ""
	@echo "Utilities:"
	@echo "  clean            Clean up test artifacts"

# Setup targets
install-test-deps:
	pip install -r test_requirements.txt

test-deps:
	python3 scripts/run_tests.py deps

# Individual test categories
test-smoke:
	python3 scripts/run_tests.py smoke

test-generation:
	python3 scripts/run_tests.py generation

test-scalability:
	python3 scripts/run_tests.py scalability

test-performance:
	python3 scripts/run_tests.py performance

test-database:
	python3 scripts/run_tests.py database

test-xs:
	python3 scripts/run_tests.py xs-generation

# Full test suite
test-full:
	python3 scripts/run_tests.py full

# Utilities
clean:
	@echo "Cleaning up test artifacts..."
	rm -rf /tmp/data_gen_test_*
	rm -rf __pycache__ scripts/__pycache__
	rm -rf .pytest_cache
	find . -name "*.pyc" -delete
	@echo "✅ Cleanup complete"

# Quick development workflow
dev-test: test-deps test-smoke
	@echo "✅ Development tests complete"

# Pre-commit checks
pre-commit: test-smoke test-xs
	@echo "✅ Pre-commit checks complete"

# Release validation
release-test: test-full
	@echo "✅ Release validation complete"
