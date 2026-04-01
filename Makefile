## FLUX Hackathon — Production Setup & Run

.PHONY: install env start stop check-deps

check-deps:
	@echo "🔍 Checking dependencies..."
	@.venv/bin/python -m pip install -r flux/requirements.txt --quiet
	@echo "✅ Dependencies verified."

env:
	@echo "🛡️  Checking environment..."
	@if [ ! -f flux/.env ]; then \
		cp flux/.env.example flux/.env && \
		echo "⚠️  Created flux/.env — please add your API keys!"; \
	else \
		echo "✅ flux/.env found."; \
	fi

start: check-deps env
	@echo "🚀 Launching FLUX (http://localhost:8501)..."
	@echo "📡 Real-time updates active below:"
	@.venv/bin/python -m streamlit run flux/app.py

stop:
	@echo "🛑 Shutting down all FLUX processes..."
	@pkill -f "streamlit run flux/app.py" || true
	@pkill -f ".venv/bin/python -m streamlit" || true
	@if [ -f streamlit.pid ]; then kill -9 `cat streamlit.pid` && rm streamlit.pid; fi
	@echo "✅ FLUX stopped."

install:
	@echo "🛠️  Initial setup into .venv..."
	@python3 -m venv .venv
	@.venv/bin/python -m pip install --upgrade pip
	@.venv/bin/python -m pip install -r flux/requirements.txt
	@echo "✅ Setup complete. Use 'make start' to run."
