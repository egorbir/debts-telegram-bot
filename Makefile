TOOLS_PATH := ./tools

############### BUILD ###############
.PHONY: versions-lock
versions-lock:
	@echo -e "Locking Deployer versions\n"
	APP_PATH=. ${TOOLS_PATH}/lock-versions.sh
