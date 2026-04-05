# Integrum V2.5 — V&V Makefile
# SaMD Compliance Rigor Automation

PROJECT_ROOT := $(shell pwd)
BACKEND_DIR := $(PROJECT_ROOT)/apps/backend
FRONTEND_DIR := $(PROJECT_ROOT)/apps/frontend
VENV := $(BACKEND_DIR)/.venv
PYTHON := $(VENV)/bin/python
DATE := $(shell date +%Y%m%d)
VV_DIR := $(PROJECT_ROOT)/docs/vv
REPORT := $(VV_DIR)/engine_coverage_report_$(DATE).txt

.PHONY: vv_golden_motors clean dev backend frontend down test

help:
	@echo "Integrum V2.5 Commands:"
	@echo "  Development:"
	@echo "    make dev              - Start backend + frontend in background"
	@echo "    make backend          - Start backend only"
	@echo "    make frontend         - Start frontend only"
	@echo "    make down             - Kill all processes and free ports"
	@echo "  Testing:"
	@echo "    make test             - Run all engine unit tests"
	@echo "    make vv_golden_motors - Run V&V for Acosta/EOSS and save report"
	@echo "  Cleanup:"
	@echo "    make clean            - Remove report artifacts"

$(VV_DIR):
	mkdir -p $(VV_DIR)

vv_golden_motors: $(VV_DIR)
	@echo "Running V&V for Golden Motors (Acosta, EOSS)..."
	@export PYTHONPATH=$(PYTHONPATH):$(BACKEND_DIR):$(BACKEND_DIR)/src && \
	$(PYTHON) -m pytest $(BACKEND_DIR)/tests/unit/engines/ \
		--cov=src.engines.acosta --cov=src.engines.eoss \
		--cov-report=term-missing > $(REPORT)
	@echo "V&V Report saved to: $(REPORT)"
	@cat $(REPORT)

clean:
	rm -rf $(VV_DIR)/*.txt

down:
	@bash scripts/cleanup.sh

dev: down
	@echo "Starting backend..."
	@cd $(BACKEND_DIR) && nohup $(PYTHON) -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --no-access-log > /tmp/uvicorn.log 2>&1 & echo "Backend PID: $$!"
	@sleep 3
	@echo "Starting frontend..."
	@cd $(FRONTEND_DIR) && nohup npm run dev -- -p 3000 > /tmp/frontend.log 2>&1 & echo "Frontend PID: $$!"
	@sleep 5
	@echo "=== Services started ==="
	@curl -s --connect-timeout 5 http://127.0.0.1:8000/health && echo "" || echo "Backend: not ready yet"
	@curl -s --connect-timeout 3 -o /dev/null -w "Frontend: HTTP %{http_code}\n" http://127.0.0.1:3000 2>/dev/null || echo "Frontend: still starting..."

backend:
	@lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null || true
	@cd $(BACKEND_DIR) && nohup $(PYTHON) -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --no-access-log > /tmp/uvicorn.log 2>&1 & echo "Backend PID: $$!"
	@sleep 3
	@curl -s --connect-timeout 5 http://127.0.0.1:8000/health && echo "" || echo "Backend: not ready yet"

frontend:
	@lsof -ti:3000 2>/dev/null | xargs kill -9 2>/dev/null || true
	@cd $(FRONTEND_DIR) && nohup npm run dev -- -p 3000 > /tmp/frontend.log 2>&1 & echo "Frontend PID: $$!"
	@sleep 5
	@curl -s --connect-timeout 3 -o /dev/null -w "Frontend: HTTP %{http_code}\n" http://127.0.0.1:3000

test:
	@cd $(BACKEND_DIR) && $(PYTHON) -m pytest tests/unit/engines/ -v --tb=short
