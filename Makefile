.PHONY: clean install clean-install

# Clean all node_modules directories in the monorepo
clean:
	@echo "Cleaning all node_modules directories..."
	@find . -name "node_modules" -type d -prune -exec rm -rf {} +
	@echo "Cleaned all node_modules directories"

# Install dependencies
install:
	@echo "Installing dependencies..."
	@bun install
	@echo "Dependencies installed"

# Clean and reinstall dependencies
clean-install: clean install
	@echo "Clean install complete"
